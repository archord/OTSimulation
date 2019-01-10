# -*- coding: utf-8 -*-
import scipy.ndimage
import numpy as np
import os
import cv2
import sys
import math
import time
from datetime import datetime
import traceback
from PIL import Image
from gwac_util import getThumbnail, genPSFView, getWindowImgs, zscale_image, getLastLine
from QueryData import QueryData
from astropy.wcs import WCS
from keras.models import load_model
from DataPreprocess import getImgStamp

from astrotools import AstroTools
from ot2classify import OT2Classify

            
class BatchImageDiff(object):
    def __init__(self, dataRoot, dataDest, tools): 
                        
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
                
        if not os.path.exists(self.tmpUpload):
            os.system("mkdir -p %s"%(self.tmpUpload))
        if not os.path.exists(self.templateDir):
            os.system("mkdir -p %s"%(self.templateDir))
        if not os.path.exists(self.tmpDir):
            os.system("mkdir -p %s"%(self.tmpDir))
        if not os.path.exists(self.tmpCat):
            os.system("mkdir -p %s"%(self.tmpCat))
        if not os.path.exists(self.resiCatDir):
            os.system("mkdir -p %s"%(self.resiCatDir))
        if not os.path.exists(self.destDir):
            os.system("mkdir -p %s"%(self.destDir))
        if not os.path.exists(self.preViewDir):
            os.system("mkdir -p %s"%(self.preViewDir))
        if not os.path.exists(self.origPreViewDir):
            os.system("mkdir -p %s"%(self.origPreViewDir))
        
    def initReg(self, idx):
        
        if idx<=0:
            idx =0
            os.system("rm -rf %s/*"%(self.tmpRoot))
            os.system("rm -rf %s/*"%(self.tmpUpload))
        
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

        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf)
        mchFile16, nmhFile16 = self.tools.runSelfMatch(self.tmpDir, self.objectImgCat, 16)
        
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
            
            #if imgIdx==492:
            #    xshift0 = 1.10
            #    yshift0 = 12.80
            
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
                    self.newImageName = self.tools.imageAlignHmg(self.tmpDir, self.objectImg, self.transHG)
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
                self.tools.sendTriggerMsg(tmsgStr)
        
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
            self.tools.sendTriggerMsg(tmsgStr)
            
            os.system("rm -rf %s/*"%(self.templateDir))
    
    
            oImgf = "%s/%s"%(self.srcDir,self.origTmplImgName)
            oImgfz = "%s/%s.fz"%(self.srcDir,self.origTmplImgName)
            if os.path.exists(oImgf):
                os.system("cp %s/%s %s/%s"%(self.srcDir, self.origTmplImgName, self.templateDir, self.templateImg))
            elif os.path.exists(oImgfz):
                os.system("cp %s/%s.fz %s/%s.fz"%(self.srcDir, self.origTmplImgName, self.templateDir, self.templateImg))
                os.system("%s %s/%s.fz"%(self.funpackProgram, self.templateDir, self.templateImg))
            else:
                self.log.warning("%s not exist"%(oImgf))
                return
                
            fieldId, ra,dec = self.tools.removeHeaderAndOverScan(self.templateDir, self.templateImg)
            sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
            fpar='sex_diff.par'
            tmplCat = self.tools.runSextractor(self.templateImg, self.templateDir, self.templateDir, fpar, sexConf, cmdStatus=0)
            
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
            self.tools.sendTriggerMsg(tmsgStr)
        
        return runSuccess
        
    def diffImage(self):
        
        starttime = datetime.now()
        
        resultFlag = True
        
        oImgPre = self.origObjectImg[:self.origObjectImg.index(".")]
        
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.badPixCat, self.tmpDir, self.badPixCat))
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImgCat, self.tmpDir, self.templateImgCat))
        
        #self.newImageName = self.tools.imageAlign(self.tmpDir, self.objectImg, self.transHG)
                
        self.objTmpResi, runSuccess = self.tools.runHotpants(self.newImageName, self.templateImg, self.tmpDir)
        if not runSuccess:
            return False

        fpar='sex_diff.par'
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        resiCat = self.tools.runSextractor(self.objTmpResi, self.tmpDir, self.tmpDir, fpar, sexConf)
        
        '''
        self.tools.runSelfMatch(self.tmpDir, resiCat, 1) #debug: get ds9 reg file
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, resiCat))
        self.log.info("resi image star %d"%(tdata.shape[0]))
        '''
        ''' '''
        mchRadius = 15 #15 10
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, resiCat, self.templateImgCat, mchRadius)
        fotProps = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
        
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, nmhFile, self.badPixCat, 1) #1 and 5 
        os.system("cp %s/%s %s/%s"%(self.tmpDir, nmhFile, self.resiCatDir, "%s.cat"%(oImgPre)))
        
        totProps = np.loadtxt("%s/%s"%(self.tmpDir, nmhFile))
        #badPixProps = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
        badPixProps = np.loadtxt("%s/%s"%(self.tmpDir, self.badPixCat))
        tstr = "badPix %d, match %d, noMatch %d"%(badPixProps.shape[0], fotProps.shape[0], totProps.shape[0])
        self.log.info(tstr)
        
        size = self.subImgSize
        if totProps.shape[0]<500 and totProps.shape[0]>0:
            
            totSubImgs, totParms = getWindowImgs(self.tmpDir, self.newImageName, self.templateImg, self.objTmpResi, totProps, size)
            tXY = totParms[:,0:2]
            tRaDec = self.wcs.all_pix2world(tXY, 1)
            totParms = np.concatenate((totParms, tRaDec), axis=1)
            fotpath = '%s/%s_totimg.npz'%(self.destDir, oImgPre)
            np.savez_compressed(fotpath, imgs=totSubImgs, parms=totParms)
            
            resiImgs = []
            for timg in totSubImgs:
                resiImgs.append(timg[2])
    
            preViewPath = "%s/%s_tot.jpg"%(self.preViewDir, oImgPre)
            #if not os.path.exists(preViewPath):
            psfView = genPSFView(resiImgs)
            Image.fromarray(psfView).save(preViewPath)
            
            if fotProps.shape[0]>0 and fotProps.shape[0]<2000:
                fotSubImgs, fotParms = getWindowImgs(self.tmpDir, self.newImageName, self.templateImg, self.objTmpResi, fotProps, size)
                tXY = fotParms[:,0:2]
                tRaDec = self.wcs.all_pix2world(tXY, 1)
                fotParms = np.concatenate((fotParms, tRaDec), axis=1)
                fotpath = '%s/%s_fotimg.npz'%(self.destDir, oImgPre)
                np.savez_compressed(fotpath, imgs=fotSubImgs, parms=fotParms)
            
            if badPixProps.shape[0]>0:
                badSubImgs, badParms = getWindowImgs(self.tmpDir, self.newImageName, self.templateImg, self.objTmpResi, badPixProps, size)
                fotpath = '%s/%s_badimg.npz'%(self.destDir, oImgPre)
                np.savez_compressed(fotpath, imgs=badSubImgs, parms=badParms)
                    
            resultFlag = True
        else:
            tmsgStr = "%s.fit resi image has %d tot objects, maybe wrong"%(oImgPre, totProps.shape[0])
            self.log.error(tmsgStr)
            self.tools.sendTriggerMsg(tmsgStr)
            resultFlag = False
            
        tgrid = 4
        tsize = 500
        tzoom = 1
        timg = getThumbnail(self.tmpDir, self.objTmpResi, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        #timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_resi.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        '''
        timg = getThumbnail(self.tmpDir, self.newImageName, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_obj.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        timg = getThumbnail(self.tmpDir, self.templateImg, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_tmp.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        '''     
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** image diff total use %d seconds"%(runTime))
        
        return resultFlag
    
    def classifyAndUpload(self):
        
        oImgPre = self.origObjectImg[:self.origObjectImg.index(".")]
        upDir = "%s/%s"%(self.tmpUpload, oImgPre)
        if not os.path.exists(upDir):
            os.system("mkdir -p %s"%(upDir))
        
        os.system("cp %s/%s %s/%s"%(self.tmpDir, self.newImageName, upDir, self.newImageName))
        os.system("cp %s/%s %s/%s"%(self.tmpDir, self.templateImg, upDir, self.templateImg))
        os.system("cp %s/%s %s/%s"%(self.tmpDir, self.objTmpResi, upDir, self.objTmpResi))
        
        totImgsName = '%s_totimg.npz'%(oImgPre)
        fotImgsName = '%s_fotimg.npz'%(oImgPre)

        self.ot2Classifier.doClassifyAndUpload(self.destDir, totImgsName, fotImgsName, 
                          upDir, self.newImageName, self.templateImg, self.objTmpResi, 
                          self.origObjectImg, self.tools.serverIP)
        
    def processImg(self, objectImg, ffNumber):

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

                regSuccess = self.register(objectImg, self.tmplImgIdx, i)
                if regSuccess:
                    diffResult = self.diffImage()
                    if diffResult == False:
                        self.diffFalseNum = self.diffFalseNum+1
                    else:
                        self.classifyAndUpload()
                    #break
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
            self.tools.sendTriggerMsg(tmsgStr)
        finally:
            if i%10==1:
                self.tools.sendTriggerMsg("imageDiff idx=%d, ffNumber=%d, %s"%(i, ffNumber, objectImg))
            i = i +1
            self.procNum = i
            if self.regFalseNum>=self.maxFalseNum:
                self.initReg(0)
                tmsgStr = "from %d %s, more than %d image regist failing, rebuilt template"%(i,objectImg,self.regFalseNum)
                self.log.error(tmsgStr)
                self.tools.sendTriggerMsg(tmsgStr)
            elif i==4*10:
                self.tmplImgIdx=0
                tmsgStr = "10 minutes, rebuilt template from %d %s"%(i,objectImg)
                self.log.info(tmsgStr)
                self.tools.sendTriggerMsg(tmsgStr)
            elif i>4*60 and i%(4*60)==1:
                self.tmplImgIdx=0
                tmsgStr = "60 minutes, rebuilt template from %d %s"%(i,objectImg)
                self.log.info(tmsgStr)
                self.tools.sendTriggerMsg(tmsgStr)
  
              
def run1(camName):
    
    #toolPath = os.getcwd()
    toolPath = '/home/gwac/img_diff_xy/image_diff'
    tools = AstroTools(toolPath)
    query = QueryData()
    
    dataDest0 = "/data/gwac_diff_xy/data"
    logDest0 = "/data/gwac_diff_xy/log"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    if not os.path.exists(logDest0):
        os.system("mkdir -p %s"%(logDest0))
    
    dayRun = 0
    nigRun = 0
    skyId = 0
    ffId = 0
    tfiles = []
    while True:
        curUtcDateTime = datetime.utcnow()
        tDateTime = datetime.utcnow()
        startDateTime = tDateTime.replace(hour=4, minute=30, second=0)  #9=17
        endDateTime = tDateTime.replace(hour=9, minute=30, second=0)  #23=7
        remainSeconds1 = (startDateTime - curUtcDateTime).total_seconds()
        remainSeconds2 = (endDateTime - curUtcDateTime).total_seconds()
        if remainSeconds1<0 and remainSeconds2>0:
            dayRun = 0
            try:
                tfiles = query.getFileList(camName, ffId)
                print(tfiles)
                for tfile in tfiles:
                    
                    curFfId = tfile[0]
                    ffNumber = tfile[1]
                    curSkyId = tfile[2]
                    timgName = tfile[3]
                    tpath = tfile[4] #/data3/G002_021_190109/G021_tom_objt_190109T13531492.fit
                    
                    srcDir= tpath[:(tpath.find(camName)-1)] #/data3/G002_021_190109
                    dateStr = srcDir[srcDir.find('G'):] #G002_021_190109
                    logfName0 = '%s/%s.log'%(logDest0, dateStr)
                    
                    if ffId==0:
                        if os.path.exists(logfName0) and os.stat(logfName0).st_size > 0:
                            tlastLine = getLastLine(logfName0)
                            if len(tlastLine)>2:
                                ffId=int(tlastLine.strip())
                                                        
                    if skyId!=curSkyId and curFfId>ffId:
                        dstDir='%s/%s'%(dataDest0, dateStr)
                        tdiff = BatchImageDiff(srcDir, dstDir, tools)
                        tStr = "start imageDiff, skyId:%s,ffNumber:%d,%s"%(curSkyId, ffNumber, timgName)
                        tdiff.log.info(tStr)
                        tdiff.tools.sendTriggerMsg(tStr)
                        
                    if curFfId>ffId:
                        skyId=curSkyId
                        ffId=curFfId
                        
                        logfile0 = open(logfName0, 'a')
                        logfile0.write("\n\n%d\n"%(ffId))
                        logfile0.close()
                        
                        tpathfz = "%s.fz"%(tpath)
                        if os.path.exists(tpath) or os.path.exists(tpathfz):
                            tdiff.processImg(timgName, ffNumber)
                        else:
                            print("%s not exist"%(tpath))
                    
            except Exception as e:
                print(str(e))
                tstr = traceback.format_exc()
                print(tstr)
                try:
                    tStr = "%s: imageDiff error, stop."%(camName)
                    tdiff.log.info(tStr)
                    tdiff.tools.sendTriggerMsg(tStr)
                except Exception as e1:
                    print(str(e1))
                    tstr = traceback.format_exc()
            if len(tfiles)==0:
                time.sleep(5)
            nigRun = nigRun+1
            #if nigRun>=3:
            #    break
        else:
            nigRun = 0
            dayRun = dayRun+1
            skyId = 0
            ffId = 0
            if dayRun%6==1:
                print("day %d wait"%(dayRun))
            time.sleep(10*60)

    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    if len(sys.argv)==2:
        camName = sys.argv[1]
        if len(camName)==4:
            run1(camName)
        else:
            print("error: camera name must like G021")
    else:
        print("run: python BatchDiff.py cameraName(G021)")
    