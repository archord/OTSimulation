# -*- coding: utf-8 -*-
import numpy as np
import os
import sys
import math
import time
from datetime import datetime
import traceback
from PIL import Image
from gwac_util import getThumbnail, genPSFView, getWindowImgs, getLastLine, selectTempOTs, filtOTs, filtByEllipticity
from QueryData import QueryData
from astropy.wcs import WCS
import pandas as pd

from astrotools import AstroTools
from ot2classify import OT2Classify
from imgSim import ImageSimulation

            
class BatchImageDiff(object):
    def __init__(self, dataRoot, dataDest, tools, camName, skyName): 
        
        self.camName = camName
        self.skyName = str(skyName)
        self.ffNumber = 0
        self.toolPath = os.getcwd()
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim"
        self.tmpUpload="/dev/shm/gwacupload"
        self.tmpDir="%s/tmp"%(self.tmpRoot)
        self.tmpCat="%s/cat"%(self.tmpRoot)
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        self.modelPath="%s/tools/mlmodel"%(self.toolPath)
        
        #self.dataRoot = "/data/gwac_data"
        self.srcDir0 = "%s"%(dataRoot)
        self.srcDir = "%s"%(dataRoot)
        
        self.resiCatDir="%s/resiCat"%(dataDest)
        self.destDir="%s/subImg"%(dataDest)
        self.preViewDir="%s/preview"%(dataDest)
        self.origPreViewDir="%s/orig_preview"%(dataDest)
            
        self.objectImg = 'oi.fit'
        self.templateImg = 'ti.fit'
        self.objectImgSim = 'ois.fit'
        self.objTmpResi = 'otr.fit'
        self.simTmpResi = 'str.fit'
        self.newImageName = "new.fit"
        
        self.badPixCat = 'badpix.cat'
        self.objectImgSimAdd = 'oisa.cat'
        self.objectImgCat = 'oi.cat'
        self.templateImgCat = 'ti.cat'
        self.objectImgSimCat = 'ois.cat'
        self.objTmpResiCat = 'otr.cat'
        self.simTmpResiCat = 'str.cat'
        
        self.imgSize = (4136, 4096)
        self.subImgSize = 21
        self.imgShape = []  
             
        self.selTemplateNum = 10 # 10 3
        self.maxFalseNum = 5
        
        self.tools = tools
        self.log = tools.log
        self.ot2Classifier = OT2Classify(self.toolPath, self.log)
        
        self.initReg(0)
                
        if not os.path.exists(self.resiCatDir):
            os.system("mkdir -p %s"%(self.resiCatDir))
        if not os.path.exists(self.destDir):
            os.system("mkdir -p %s"%(self.destDir))
        if not os.path.exists(self.preViewDir):
            os.system("mkdir -p %s"%(self.preViewDir))
        if not os.path.exists(self.origPreViewDir):
            os.system("mkdir -p %s"%(self.origPreViewDir))

    def sendMsg(self, tmsg):
        
        tmsgStr = "%s, sky:%s, ffNum:%d\n %s"%(self.camName, self.skyName, self.ffNumber, tmsg)
        self.tools.sendTriggerMsg(tmsgStr)
    
    def initReg(self, idx):
        
        if idx<=0:
            idx =0
            os.system("rm -rf %s/*"%(self.tmpRoot))
            os.system("rm -rf %s/*"%(self.tmpUpload))
            if not os.path.exists(self.tmpUpload):
                os.system("mkdir -p %s"%(self.tmpUpload))
            if not os.path.exists(self.templateDir):
                os.system("mkdir -p %s"%(self.templateDir))
            if not os.path.exists(self.tmpDir):
                os.system("mkdir -p %s"%(self.tmpDir))
            if not os.path.exists(self.tmpCat):
                os.system("mkdir -p %s"%(self.tmpCat))
        
        self.procNum = 0
        self.tmplImgIdx = 0
        self.regFalseNum = 0
        self.diffFalseNum = 0
        self.origTmplImgName = ""
        self.regFalseIdx = 0
        self.makeTempFalseNum = 0
        self.imglist = []
        self.transHGs = []
        
        
    def register(self, imgName, regIdx, imgIdx):
        
        starttime = datetime.now()
        
        regSuccess = True
        imgpre= imgName.split(".")[0]
        regCatName = "%s.cat"%(imgpre)
        self.origObjectImg = imgName
        os.system("rm -rf %s/*"%(self.tmpDir))
        
        oImgf = "%s/%s.fit"%(self.srcDir,imgpre)
        oImgfz = "%s/%s.fit.fz"%(self.srcDir,imgpre)
        if os.path.exists(oImgf):
            os.system("cp %s/%s.fit %s/%s"%(self.srcDir, imgpre, self.tmpDir, self.objectImg))
        elif os.path.exists(oImgfz):
            os.system("cp %s/%s.fit.fz %s/%s.fz"%(self.srcDir, imgpre, self.tmpDir, self.objectImg))
            os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, self.objectImg))
        else:
            self.log.warning("%s not exist"%(oImgf))
            return False
                
        self.tools.removeHeaderAndOverScan(self.tmpDir,self.objectImg)

        #sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']
        fpar='sex_diff.par'
        self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf)
        mchFile16, nmhFile16 = self.tools.runSelfMatch(self.tmpDir, self.objectImgCat, 16)
        self.osn16 = nmhFile16
        
        tobjImgCat = nmhFile16
        os.system("cp %s/%s %s/%s"%(self.tmpDir, tobjImgCat, self.tmpCat, regCatName))
        
        xrms=0
        yrms=0
        tImgNum = len(self.imglist)
        if tImgNum ==0:
            self.imglist.append((regCatName, 0, 0, 0, 0, 0, 99))
            self.transHGs.append([])
        else:
            if tImgNum==1:
                xshift0, yshift0 = 0, 0
            else:
                timgN = self.imglist[-1]
                transHGN = self.transHGs[-1]
                if regIdx==tImgNum-1:
                    xshift0, yshift0 = 0, 0
                elif regIdx==timgN[1]:
                    xshift0 = timgN[2]
                    yshift0 = timgN[3]
                else:
                    timgNk = self.imglist[regIdx]
                    xshift0 = timgN[2] - timgNk[2]
                    yshift0 = timgN[3] - timgNk[3]
                    transHGN = []
                        
            tImgCat = self.imglist[regIdx][0]
            os.system("cp %s/%s %s/%s"%(self.tmpCat, tImgCat, self.tmpDir, self.templateImgCat))
            
            tmsgStr = "%d,%s regist to %d,%s, fwhm %.2f"%(tImgNum, imgName, regIdx, tImgCat, self.imglist[regIdx][6])
            self.log.info(tmsgStr)
                        
            xshift0Orig = xshift0
            yshift0Orig = yshift0
            tryShifts = [1.0,0.1]
            for tsf in tryShifts:
                if math.fabs(xshift0)>0.000001 and math.fabs(yshift0)>0.000001:
                    xshift0 = tsf*xshift0Orig
                    yshift0 = tsf*yshift0Orig
                    tobjImgCatShift = self.tools.catShift(self.tmpDir, tobjImgCat, xshift0, yshift0, transHGN)
                else:
                    tobjImgCatShift = tobjImgCat
                
                mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, tobjImgCatShift, self.templateImgCat, 10)
                osn16_tsn16_cm = mchFile
                osn16_tsn16_cm_pair = mchPair
                
                #tNumMean, tNumMin, tNumRms = self.tools.gridStatistic(self.tmpDir, osn16_tsn16_cm, self.imgSize, gridNum=4)
                fwhmMean, fwhmRms = self.tools.fwhmEvaluate(self.tmpDir, osn16_tsn16_cm)
                
                self.transHG, xshift, yshift, xrms, yrms = self.tools.getMatchPosHmg(self.tmpDir, tobjImgCat, self.templateImgCat, osn16_tsn16_cm_pair)
                if xrms<1 and yrms<1 and imgIdx>=self.selTemplateNum:
                    self.newImageName, self.objectImgCatTrans = self.tools.imageAlignHmg(self.tmpDir, self.objectImg, self.objectImgCat, self.transHG)
                self.log.info("homography astrometry pos transform, xshift0=%.2f, yshift0=%.2f"%(xshift0, yshift0))
                self.log.info("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
                
                if xrms<1 and yrms<1:
                    break
                else:
                    if math.fabs(xshift0)>0.000001 and math.fabs(yshift0)>0.000001:
                        transHGN = []
                        self.log.error("astrometry error, shift scale %.1f, retry"%(tsf))
                    else:
                        break
            
            if xrms<1 and yrms<1:
                tinfo = (regCatName, regIdx, xshift, yshift, xrms, yrms, fwhmMean)
                self.imglist.append(tinfo)
                self.transHGs.append(self.transHG)
                self.log.info(tinfo)
            else:
                self.imglist.append((regCatName, regIdx, 0, 0, 0, 0, 99))
                self.transHGs.append([])
                regSuccess = False
                tmsgStr = "%d %s astrometry failing"%(imgIdx, imgName)
                self.log.error(tmsgStr)
                self.sendMsg(tmsgStr)
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** regist %s use %d seconds"%(imgName, runTime))
    
        return regSuccess
    
    def makeTemplate(self):
        
        try:
            starttime = datetime.now()
            
            os.system("rm -rf %s/*"%(self.templateDir))
            
            selTempRange = self.selTemplateNum
            tImgNum = len(self.imglist)
            if tImgNum>=4*60:
                selTempRange=4*30
                endIdx = tImgNum-30
            else:
                endIdx = tImgNum
            
            startIdx = tImgNum-selTempRange
            if startIdx<0:
                startIdx = 0
            timgN = self.imglist[-1]
            timgNk = self.imglist[startIdx]
            if timgN[1]!=timgNk[1]: #check if rebuilt template
                for tIdx in range(startIdx,tImgNum):
                    timgNm = self.imglist[tIdx]
                    if timgN[1]==timgNm[1]:
                        startIdx = tIdx
                        if startIdx>endIdx:
                            endIdx = tImgNum
                        break
                if startIdx == tImgNum-selTempRange:
                    startIdx=tImgNum-1
                    endIdx = tImgNum
                    
            tparms = []
            for tIdx in range(startIdx,endIdx):
                tparms.append(self.imglist[tIdx])
                
            tparms = np.array(tparms)
            self.log.debug(tparms)
            tfwhms = tparms[:,6].astype(np.float)
            minIdx = np.argmin(tfwhms)
            
            timgCat = tparms[minIdx][0]
            imgpre= timgCat.split(".")[0]
            self.origTmplImgName = "%s.fit"%(imgpre)
            self.tmplImgIdx = startIdx + minIdx
            
            tmsgStr = "select %dth image %s as template, it has min fwhm %.2f"%(self.tmplImgIdx, self.origTmplImgName, tfwhms[minIdx])
            self.log.info(tmsgStr)
            self.sendMsg(tmsgStr)
            
            os.system("rm -rf %s/*"%(self.templateDir))
    
    
            oImgf = "%s/%s"%(self.srcDir,self.origTmplImgName)
            oImgfz = "%s/%s.fz"%(self.srcDir,self.origTmplImgName)
            fileExist = True
            if os.path.exists(oImgf):
                os.system("cp %s/%s %s/%s"%(self.srcDir, self.origTmplImgName, self.templateDir, self.templateImg))
            elif os.path.exists(oImgfz):
                os.system("cp %s/%s.fz %s/%s.fz"%(self.srcDir, self.origTmplImgName, self.templateDir, self.templateImg))
                os.system("%s %s/%s.fz"%(self.funpackProgram, self.templateDir, self.templateImg))
            else:
                self.log.warning("%s not exist"%(oImgf))
                fileExist = False
                runSuccess = False
            
            if fileExist:
                fieldId, ra,dec = self.tools.removeHeaderAndOverScan(self.templateDir, self.templateImg)
                sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']
                fpar='sex_diff.par'
                self.templateImgCat = self.tools.runSextractor(self.templateImg, self.templateDir, self.templateDir, fpar, sexConf, cmdStatus=0)
                mchFile, nmhFile = self.tools.runSelfMatch(self.templateDir, self.templateImgCat, 16)
                self.tsn16 = nmhFile
                '''
                sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5','-CATALOG_TYPE', 'FITS_LDAC']
                tmplCat = self.tools.runSextractor(self.templateImg, self.templateDir, self.templateDir, fpar, sexConf, cmdStatus=0, outSuffix='_ldac.fit')
                
                self.tools.ldac2fits('%s/%s'%(self.templateDir,tmplCat), '%s/ti_cat.fit'%(self.templateDir))
                
                #tpath = "%s/%s"%(self.templateDir,tmplCat)
                #self.tools.runWCS(self.templateDir,'ti_cat.fit', ra, dec)
                ccdName = self.origTmplImgName[:4]
                runSuccess = self.tools.runWCSRemotePC780(self.templateDir,'ti_cat.fit', ra, dec, ccdName)
                
                if runSuccess:
                    self.wcs = WCS('%s/ti_cat.wcs'%(self.templateDir))
                    ra_center, dec_center = self.wcs.all_pix2world(self.imgSize[1]/2, self.imgSize[0]/2, 1)
                    self.log.info('read_ra_center:%.5f, read_dec_center:%.5f'%(ra, dec))
                    self.log.info('real_ra_center:%.5f, real_dec_center:%.5f'%(ra_center, dec_center))
                else:
                    self.wcs = []
                    self.log.error('make template %s, get wcs error'%(self.origTmplImgName))
                '''
                objName = 'ti.fit'
                bkgName = 'ti_bkg.fit'
                self.badPixCat = self.tools.processBadPix(objName, bkgName, self.templateDir, self.templateDir)
                
                #do astrometry, get wcs    
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("********** make template %s use %d seconds"%(self.origTmplImgName, runTime))
            
        except Exception as e:
            runSuccess = False
            self.origTmplImgName = ''
            self.tmplImgIdx = 0
            tstr = traceback.format_exc()
            self.log.error(tstr)
            tmsgStr = "make template error"
            self.sendMsg(tmsgStr)
        
        return runSuccess
        
    def diffImage(self):
        
        starttime = datetime.now()
                
        oImgPre = self.origObjectImg[:self.origObjectImg.index(".")]
        
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.badPixCat, self.tmpDir, self.badPixCat))
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.tsn16, self.tmpDir, self.tsn16))
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, self.objectImgCat))
        print("objImg extract star %d"%(tdata.shape[0]))
        if len(tdata.shape)<2 or tdata.shape[0]<5000:
            print("%s has too little stars, break this run"%(self.objectImg))
            return
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, self.templateImgCat))
        print("tempImg extract star %d"%(tdata.shape[0]))
        if len(tdata.shape)<2 or tdata.shape[0]<5000:
            print("%s has too little stars, break this run"%(self.objectImg))
            return

        mchFile, nmhFile = self.tools.runSelfMatch(self.objectImgCat, 24)
        self.osn32 = nmhFile

        osn16s = selectTempOTs(self.osn16, self.tmpDir)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, osn16s))
        if len(tdata.shape)<2 or tdata.shape[0]<100:
            print("%s has too little stars, break this run"%(self.objectImg))
            return np.array([]), np.array([])
        
        osn16sf = filtOTs(osn16s, self.tmpDir)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, osn16sf))
        if len(tdata.shape)<2 or tdata.shape[0]<45:
            print("%s has too little stars, break this run"%(self.objectImg))
            return np.array([]), np.array([])
        
        osn32f = filtOTs(self.osn32, self.tmpDir)
                
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(osn32f, self.tsn16, 5)
        osn32s_tsn5_cm5 = mchFile
        osn32s_tsn5_cm5_pair = mchPair
        
        totalTOT = 1000
        subImgBuffer = []
        objS2NBuffer = []
        tnum = 0
        imgSimClass = ImageSimulation()
        
        ii = 1
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        while tnum<totalTOT:
            simFile, simPosFile, simDeltaXYA, tmpOtImgs = imgSimClass.simulateImage1(osn32f, self.objectImg, osn16sf, self.objectImg)
            self.objectImgSim = simFile
            self.objectImgSimAdd = simPosFile
            
            self.runSextractor(self.objectImgSim)
            
            self.simTmpResi = self.tools.runHotpants(self.objectImgSim, self.templateImg)
            self.simTmpResiCat = self.tools.runSextractor(self.simTmpResi, sexConf)
            
            simTmpResiCatEf = filtByEllipticity(self.simTmpResiCat, self.tmpDir, maxEllip=0.5)
            mchFile, nmhFile = self.tools.runSelfMatch(simTmpResiCatEf, 16)
            simTmpResiCatEf_sn32 = nmhFile
            #simTmpResiCatEf_sn32 = simTmpResiCatEf
            
            mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.objectImgSimAdd, simTmpResiCatEf_sn32, self.r5)
            str_oisa_cm5 = mchFile
            str_oisa_cm5_pair = mchPair
            
            
            tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, osn32s_tsn5_cm5_pair)).astype(np.int)
            tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, str_oisa_cm5_pair)).astype(np.int)
            tIdx1 = tIdx1 - 1
            tIdx2 = tIdx2 - 1
            self.log.debug("objectCat matched data %d, ResiCat matched data %d"%(tIdx1.shape[0], tIdx2.shape[0]))
                    
            tnames1 = ['objId', 'tmpId']
            tnames2 = ['objId', 'resiId']
            
            #unionIdx = np.intersect1d(tIdx1[:,0], tIdx2[:,0])  #union1d
            #self.log.debug("intersect objectCat and templateCat matched data: %d"%(unionIdx.shape[0]))
            
            df1 = pd.DataFrame(data=tIdx1, columns=tnames1)
            df2 = pd.DataFrame(data=tIdx2, columns=tnames2)
            unionIdx=pd.merge(df1, df2, how='inner', on=['objId'])
            self.log.debug("innerjoin objectCat and templateCat matched data %d"%(unionIdx.shape[0]))
            
            tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, self.objectImgSimAdd))
            tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, self.tsn16))
            tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, simTmpResiCatEf_sn32))
            
            simDeltaXYA = np.array(simDeltaXYA)
            tdeltaXYA = simDeltaXYA[unionIdx["objId"].values]
            tdata11 = tdata1[unionIdx["objId"].values]
            tdata12 = tdata2[unionIdx["tmpId"].values]
            tdata22 = tdata3[unionIdx["resiId"].values]
            
            poslist = np.concatenate(([tdata11[:,0]], [tdata11[:,1]], 
                                      [tdata12[:,3]+tdeltaXYA[:,0]], [tdata12[:,4]+tdeltaXYA[:,1]], 
                                      [tdata22[:,0]], [tdata22[:,1]]), axis=0).transpose()
            #print(poslist)
            #genFinalOTDs9Reg('tot', self.tmpDir, poslist)
            size = self.subImgSize
            subImgs = self.getWindowImgs(self.objectImgSim, self.templateImg, self.simTmpResi, poslist, size)
            #subImgs = self.getWindowImgs(self.objectImgSimSubBkg, self.templateImgSubBkg, self.simTmpResi, poslist, size)
            tnum = tnum + len(subImgs)
            
            subImgBuffer.extend(subImgs)
            objS2NBuffer.extend(tdata22[:,3].tolist())
            
            self.log.info("\n******************")
            self.log.info("run %d, total sub image %d"%(ii, tnum))
            if ii>6:
                break
            ii = ii + 1
            #break
        
        subImgs = np.array(subImgBuffer)
        objS2NBuffer = np.array(objS2NBuffer)
        print(subImgs.shape)
        print(objS2NBuffer.shape)

        #pickle
        totpath = '%s/%s_otimg_tot%d.npz'%(self.destDir, oImgPre, subImgs.shape[0])
        np.savez_compressed(totpath, tot=subImgs, ts2n=objS2NBuffer)
        
        print("%s with TOT %d"%(oImgPre, subImgs.shape[0]))
        
    def processImg(self, objectImg, ffNumber):

        self.ffNumber = ffNumber
        i = self.procNum
        try:
            self.log.debug("\n\n************%d, %s"%(i, objectImg))
            if i<self.selTemplateNum:
                self.register(objectImg, i-1, i)
            else:
                if self.tmplImgIdx==0:
                    tempSuccess = self.makeTemplate()
                    if not tempSuccess:
                        self.makeTempFalseNum = self.makeTempFalseNum + 1
                        self.log.error("make template error %d %s"%(i, objectImg))
                    else:
                        self.makeTempFalseNum = 0

                if len(self.origTmplImgName)>0:
                    regSuccess = self.register(objectImg, self.tmplImgIdx, i)
                    if regSuccess:
                        diffResult = self.diffImage()
                        if diffResult == False:
                            self.diffFalseNum = self.diffFalseNum+1
                    else:
                        if self.regFalseIdx+self.regFalseNum==i:
                            self.regFalseNum = self.regFalseNum +1
                        else:
                            self.regFalseIdx=i
                            self.regFalseNum = 1
                        
        except Exception as e:
            tstr = traceback.format_exc()
            self.log.error(tstr)
            tmsgStr = "process %d %s error"%(i,objectImg)
            self.sendMsg(tmsgStr)
        finally:
            i = i +1
            self.procNum = i
            if self.regFalseNum>=self.maxFalseNum:
                tmsgStr = "from %d %s, more than %d image regist failing, rebuilt template"%(i,objectImg,self.regFalseNum)
                self.initReg(0)
                self.log.error(tmsgStr)
                self.sendMsg(tmsgStr)
            elif self.makeTempFalseNum>=self.maxFalseNum:
                tmsgStr = "from %d %s, more than %d image make template failing, rebuilt template"%(i,objectImg,self.regFalseNum)
                self.initReg(0)
                self.log.info(tmsgStr)
                self.sendMsg(tmsgStr)
            elif i==4*10:
                self.tmplImgIdx=0
                tmsgStr = "10 minutes, rebuilt template from %d %s"%(i,objectImg)
                self.log.info(tmsgStr)
                self.sendMsg(tmsgStr)
            elif i==4*30:
                self.tmplImgIdx=0
                tmsgStr = "30 minutes, rebuilt template from %d %s"%(i,objectImg)
                self.log.info(tmsgStr)
                self.sendMsg(tmsgStr)
                
            elif i>4*60 and i%(4*60)==1:
                self.tmplImgIdx=0
                tmsgStr = "%d hours, rebuilt template from %d %s"%(i/(4*60), i,objectImg)
                self.log.info(tmsgStr)
                self.sendMsg(tmsgStr)
                ''''''

    def batchSim(self):
        
        camName = "G044"
        curSkyId = "abcd"
        srcDir = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0"
        dstDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data_1227"
        
        toolPath = os.getcwd()
        tools = AstroTools(toolPath)
        tdiff = BatchImageDiff(srcDir, dstDir, tools, camName, curSkyId)
        
        flist = os.listdir(self.srcDir)
        flist.sort()
        
        imgs = []
        for tfilename in flist:
            if tfilename.find("fit")>-1 and tfilename.find("temp")==-1:
                imgs.append(tfilename)
        
        for i, timg in enumerate(imgs):
                
            if i>50 and i < 600:
                print("\n\nprocess %s"%(timg))
                tdiff.processImg(timg, i)
                #break
            else:
                continue
            
if __name__ == "__main__":
    
    otsim = BatchImageDiff()
    otsim.batchSim()
    