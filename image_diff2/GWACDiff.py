# -*- coding: utf-8 -*-
import numpy as np
import os
import sys
import math
import time
from datetime import datetime
import traceback
from astropy.io import fits
from PIL import Image
from gwac_util import getThumbnail, genPSFView, getWindowImgs, getLastLine
from QueryData import QueryData
from astropy.wcs import WCS

from astrotools import AstroTools
from ot2classify import OT2Classify
from blindmatch import doAll

            
class GWACDiff(object):
    
    objectImg = 'oi.fit'
    templateImg = 'ti.fit'
    objTmpResi = 'otr.fit'
    newImageName = "new.fit"
    
    badPixCat = 'badpix.cat'
    objectImgCat = 'oi.cat'
    templateImgCat = 'ti.cat'
    objTmpResiCat = 'otr.cat'
    
    imgSize = (4136, 4096)
    subImgSize = 21
    imgShape = []  
         
    maxFalseNum = 5
        
    def __init__(self, dataDest, tools): 
        
        self.tools = tools
        self.toolPath = tools.rootPath
        self.log = tools.log
        
        self.modelPath="%s/tools/mlmodel"%(self.toolPath)
        #self.modelName='model_128_5_RealFOT_8_190111.h5'
        #self.modelName='model_RealFOT_64_100_fot10w_20190122_dropout.h5'
        self.modelName='model_80w_20190403_branch3_train12_79.h5'
        self.ot2Classifier = OT2Classify(self.toolPath, self.log, self.modelName)
        
        self.ffNumber = 0
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim"
        self.tmpUpload="/dev/shm/gwacupload"
        self.tmpDir="%s/tmp"%(self.tmpRoot)
        self.tmpCat="%s/cat"%(self.tmpRoot)
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        self.tmpAlign="%s/align"%(self.tmpRoot)
        
        self.initReg(0)
        
        self.catDir="%s/A_cat"%(dataDest)
        self.tmplAlignDir="%s/B_template_align"%(dataDest)
        self.alignDir="%s/C_align"%(dataDest)
        self.cmbDir="%s/D_combine5"%(dataDest)
        self.cmbCatDir="%s/E_combine5Cat"%(dataDest)
        self.tmplDiffDir="%s/F_template_diff"%(dataDest)
        self.diffImgDir="%s/G_diffImg"%(dataDest)
        self.diffCatDir="%s/H_diffCat"%(dataDest)
        self.origPreViewDir="%s/I_origPreview"%(dataDest)
            
        if not os.path.exists(self.catDir):
            os.system("mkdir -p %s"%(self.catDir))
        if not os.path.exists(self.tmplAlignDir):
            os.system("mkdir -p %s"%(self.tmplAlignDir))
        if not os.path.exists(self.alignDir):
            os.system("mkdir -p %s"%(self.alignDir))
        if not os.path.exists(self.cmbDir):
            os.system("mkdir -p %s"%(self.cmbDir))
        if not os.path.exists(self.cmbCatDir):
            os.system("mkdir -p %s"%(self.cmbCatDir))
        if not os.path.exists(self.tmplDiffDir):
            os.system("mkdir -p %s"%(self.tmplDiffDir))
        if not os.path.exists(self.diffImgDir):
            os.system("mkdir -p %s"%(self.diffImgDir))
        if not os.path.exists(self.diffCatDir):
            os.system("mkdir -p %s"%(self.diffCatDir))
        if not os.path.exists(self.origPreViewDir):
            os.system("mkdir -p %s"%(self.origPreViewDir))

    def sendMsg(self, tmsg):
        
        tmsgStr = "%s, sky:%s, ffNum:%d\n %s"%(self.camName, self.skyName, self.ffNumber, tmsg)
        self.tools.sendTriggerMsg(tmsgStr)
    
    def initReg(self, idx):
        
        if not os.path.exists(self.tmpRoot):
            os.system("mkdir -p %s"%(self.tmpRoot))
                
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
            if not os.path.exists(self.tmpAlign):
                os.system("mkdir -p %s"%(self.tmpAlign))
                
        
    def getCat(self, srcDir, imgName, destDir):
        
        starttime = datetime.now()
        
        isSuccess = False
        imgpre= imgName.split(".")[0]
        os.system("rm -rf %s/*"%(self.tmpDir))
        objectImg = 'oi.fit'
        
        oImgf = "%s/%s.fit"%(srcDir,imgpre)
        oImgfz = "%s/%s.fit.fz"%(srcDir,imgpre)
        if os.path.exists(oImgf):
            os.system("cp %s/%s.fit %s/%s"%(srcDir, imgpre, self.tmpDir, objectImg))
        elif os.path.exists(oImgfz):
            os.system("cp %s/%s.fit.fz %s/%s.fz"%(srcDir, imgpre, self.tmpDir, objectImg))
            os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, objectImg))
        else:
            self.log.warning("%s not exist"%(oImgf))
            return False
                
        skyName, ra,dec = self.tools.removeHeaderAndOverScan(self.tmpDir,objectImg)

        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        #sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        fpar='sex_diff.par'
        objectImgCat = self.tools.runSextractor(objectImg, self.tmpDir, self.tmpDir, fpar, sexConf)
        if os.path.exists("%s/%s"%(self.tmpDir, objectImgCat)):
            isSuccess = True
            os.system("cp %s/%s %s/%s.cat"%(self.tmpDir, objectImgCat, destDir, imgpre))
            starNum, fwhmMean, fwhmRms, bgMean, bgRms = self.tools.basicStatistic(self.tmpDir, objectImgCat)
        else:
            starNum, fwhmMean, fwhmRms, bgMean, bgRms = 0,0,0,0,0
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** getCat %s use %d seconds"%(imgName, runTime))
    
        return isSuccess, skyName, starNum, fwhmMean, bgMean
    
    def getAlignTemplate(self, tmplParms, skyName):
        
        starttime = datetime.now()
        tmplRoot = '/data/gwac_data/gwac_wcs_idx'
        status = tmplParms[0]
        files = tmplParms[1]
        imgName = ''
        if status ==2: #no history template, select template from current observed image
            imgName = files[0][0]
            imgpre = imgName.split(".")[0]
            os.system("cp %s/%s.cat %s/%s.cat"%(self.catDir, imgpre, self.tmplAlignDir, imgpre))
        elif status==1:
            #/data/gwac_data/gwac_wcs_idx/00900085/G002_021/181028/G043_mon_objt_181018T18572921.fit
            tfullPaths = []
            for tfile in files:
                imgName = tfile[0]
                dateStr = tfile[1]
                camName = imgName[:4]
                mountCam = "G%03d_%s"%(int(camName[1:3]),camName[1:])
                
                imgpre = imgName.split(".")[0]
                tpath = "%s/%s/%s/%s"%(tmplRoot, skyName, mountCam, dateStr)
                tfullPaths.append("%s/%s.fit"%(tpath,imgpre))
                tfullPaths.append("%s/%s.wcs"%(tpath,imgpre))
                tfullPaths.append("%s/%s.cat"%(tpath,imgpre))
                tfullPaths.append("%s/%s_badpix.cat"%(tpath,imgpre))
                tfullPaths.append("%s/%s_cat.fit"%(tpath,imgpre))
                break #only get the first template file
            self.tools.remoteGetFile(tfullPaths, self.tmplAlignDir)
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** getAlignTemplate %s use %d seconds"%(imgName, runTime))
    
    def alignImage(self, srcDir, imgName, tmplParms):
        
        starttime = datetime.now()
        
        files = tmplParms[1]
        templateImg = files[0][0] #self.tmplAlignDir
        
        isSuccess = False
        imgpre= imgName.split(".")[0]
        os.system("rm -rf %s/*"%(self.tmpAlign))
        objectImg = 'oi.fit'
        objectCat = 'oi.cat'
        ttmplCat = 'ti.cat'
        
        oImgf = "%s/%s.fit"%(srcDir,imgpre)
        oImgfz = "%s/%s.fit.fz"%(srcDir,imgpre)
        if os.path.exists(oImgf):
            os.system("cp %s/%s.fit %s/%s"%(srcDir, imgpre, self.tmpAlign, objectImg))
        elif os.path.exists(oImgfz):
            os.system("cp %s/%s.fit.fz %s/%s.fz"%(srcDir, imgpre, self.tmpAlign, objectImg))
            os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpAlign, objectImg))
        else:
            self.log.warning("%s not exist"%(oImgf))
                
        skyName, ra,dec = self.tools.removeHeaderAndOverScan(self.tmpAlign,objectImg)
        os.system("cp %s/%s.cat %s/%s"%(self.catDir, imgpre, self.tmpAlign, objectCat))
        os.system("cp %s/%s.cat %s/%s"%(self.tmplAlignDir, templateImg.split(".")[0] , self.tmpAlign, ttmplCat))
        alignRst = doAll(self.tmpAlign, ttmplCat, self.tmpAlign, objectCat, self.tmpAlign, objectImg, self.alignDir)
        if alignRst[0]>0:
            totalMatchNum, xshift,yshift, xrotation, yrotation, blindStarNum, mchRatios = alignRst
            self.log.info(alignRst)
            isSuccess = True
    
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** getCat %s use %d seconds"%(imgName, runTime))
        return isSuccess
        
    def superCombine(self, imgs, regions=[2,2]):
    
        try:
            starttime = datetime.now()
            
            tCmbImg = np.array([])
            regWid = 0
            regHei = 0
            for ty in range(regions[0]):
                for tx in range(regions[1]):
                    imgs = []
                    for j in range(len(imgs)):
                        tname = imgs[j]
                        tdata1 = fits.getdata("%s/%s"%(self.tmpAlign, tname),ext=0) #first image is template
                        if tCmbImg.shape[0]==0:
                            tCmbImg=np.zeros(tdata1.shape, dtype=np.uint16)
                            regWid = int(tCmbImg.shape[1]/2)
                            regHei = int(tCmbImg.shape[0]/2)
                        imgs.append(tdata1[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid].copy())

                    imgArray = np.array(imgs)
                    tCmbImg[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid] = np.median(imgArray,axis=0)
            
            #tCmbImg = tCmbImg.astype(np.uint16)
            outImgName = "%s_cmb%03d.fit"%(imgs[0].split('.')[0], len(imgs))
            fits.writeto("%s/%s"%(self.cmbDir, outImgName), tCmbImg, overwrite=True)
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            print("combine use %d seconds"%(runTime))
            
        except Exception as e:
            outImgName = ''
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        return outImgName
            
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
            self.sendMsg(tmsgStr)
        
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
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, resiCat, self.objectImgCatTrans, 1) #1 and 5 
        badPixProps2 = np.loadtxt("%s/%s"%(self.tmpDir, nmhFile))
        
        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
        tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, self.objectImgCatTrans))
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair)).astype(np.int)
        tIdx1 = tIdx1 - 1
        origData = tdata2[tIdx1[:,1]]
        
        if origData.shape[0]==tdata1.shape[0]:
            outCatName = "%s_orgpos.cat"%(mchFile[:mchFile.index(".")])
            outCatPath = "%s/%s"%(self.tmpDir, outCatName)
            tstr=""
            i=0
            for td in tdata1:
               tstr += "%.4f %.4f %.2f %.2f %.2f %.3f %.3f %.3f %.2f %.2f %d %.4f %.4f %.4f %.4f\n"%\
                  (td[0],td[1],td[2],td[3],td[4],td[5],td[6],td[7],td[8],td[9],td[10],origData[i][11], origData[i][12], origData[i][13], origData[i][14])
               i=i+1
            fp0 = open(outCatPath, 'w')
            fp0.write(tstr)
            fp0.close()
            mchFile = outCatName
        else:
            self.log.error("add orig pos error")
        
        '''
        self.tools.runSelfMatch(self.tmpDir, resiCat, 1) #debug: get ds9 reg file
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, resiCat))
        self.log.info("resi image star %d"%(tdata.shape[0]))
        '''
        ''' '''
        mchRadius = 15 #15 10
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, mchFile, self.templateImgCat, mchRadius)
        fotProps = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
        
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, nmhFile, self.badPixCat, 1) #1 and 5 
        os.system("cp %s/%s %s/%s"%(self.tmpDir, nmhFile, self.resiCatDir, "%s.cat"%(oImgPre)))
        
        totProps = np.loadtxt("%s/%s"%(self.tmpDir, nmhFile))
        #badPixProps = np.loadtxt("%s/%s"%(self.tmpDir, self.badPixCat))
        badPixProps = np.array([])
        tstr = "orgBadPix %d, nmBad %d, match %d, noMatch %d"%(badPixProps.shape[0], badPixProps2.shape[0], fotProps.shape[0], totProps.shape[0])
        self.log.info(tstr)
        
        #size = self.subImgSize
        size = 68
        if totProps.shape[0]<500 and totProps.shape[0]>0:
            
            totSubImgs, totParms = getWindowImgs(self.tmpDir, self.newImageName, self.templateImg, self.objTmpResi, totProps, size)
            if totParms.shape[0]>0:
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
                if fotParms.shape[0]>0:
                    tXY = fotParms[:,0:2]
                    tRaDec = self.wcs.all_pix2world(tXY, 1)
                    fotParms = np.concatenate((fotParms, tRaDec), axis=1)
                    fotpath = '%s/%s_fotimg.npz'%(self.destDir, oImgPre)
                    np.savez_compressed(fotpath, imgs=fotSubImgs, parms=fotParms)
            '''
            if badPixProps.shape[0]>0:
                badSubImgs, badParms = getWindowImgs(self.tmpDir, self.newImageName, self.templateImg, self.objTmpResi, badPixProps, size)
                if badParms.shape[0]>0:
                    fotpath = '%s/%s_badimg.npz'%(self.destDir, oImgPre)
                    np.savez_compressed(fotpath, imgs=badSubImgs, parms=badParms)
            
            if badPixProps2.shape[0]>0:
                badSubImgs, badParms = getWindowImgs(self.tmpDir, self.newImageName, self.templateImg, self.objTmpResi, badPixProps2, size)
                if badParms.shape[0]>0:
                    fotpath = '%s/%s_badimg2.npz'%(self.destDir, oImgPre)
                    np.savez_compressed(fotpath, imgs=badSubImgs, parms=badParms)
            '''        
            resultFlag = True
        else:
            tmsgStr = "%s.fit resi image has %d tot objects, maybe wrong"%(oImgPre, totProps.shape[0])
            self.log.error(tmsgStr)
            #self.sendMsg(tmsgStr)
            resultFlag = False
        
        '''
        tgrid = 4
        tsize = 500
        tzoom = 1
        timg = getThumbnail(self.tmpDir, self.objTmpResi, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        #timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_resi.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        '''
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
        
    def processImg(self, dataRoot, objectImg, ffNumber):
        
        self.srcDir = "%s"%(dataRoot)

        self.ffNumber = ffNumber
        i = self.procNum
        try:
            self.log.debug("\n\n************%d, %s"%(i, objectImg))
            if i<self.selTemplateNum or self.regSuccessNum<self.selTemplateNum:
                regSuccess = self.register(objectImg, i-1, i)
                if not regSuccess:
                    self.regSuccessNum=0
                    if self.regFalseIdx+self.regFalseNum==i:
                        self.regFalseNum = self.regFalseNum +1
                    else:
                        self.regFalseIdx=i
                        self.regFalseNum = 1
                else:
                    self.regSuccessNum = self.regSuccessNum +1
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
    
    startProcess = False
    dayRun = 0
    nigRun = 0
    skyId = 0
    ffId = 0
    tfiles = []
    while True:
        curUtcDateTime = datetime.utcnow()
        tDateTime = datetime.utcnow()
        '''
        startDateTime = tDateTime.replace(hour=9, minute=30, second=0)  #9=17  1=9
        endDateTime = tDateTime.replace(hour=22, minute=30, second=0)  #22=6    8=16
        remainSeconds1 = (startDateTime - curUtcDateTime).total_seconds()
        remainSeconds2 = (endDateTime - curUtcDateTime).total_seconds()
        if remainSeconds1<0 and remainSeconds2>0:
        '''
        startDateTime = tDateTime.replace(hour=8, minute=0, second=0)  #9=17  1=9
        endDateTime = tDateTime.replace(hour=9, minute=0, second=0)  #22=6    8=16
        remainSeconds1 = (startDateTime - curUtcDateTime).total_seconds()
        remainSeconds2 = (endDateTime - curUtcDateTime).total_seconds()
        if not (remainSeconds1<0 and remainSeconds2>0):
            dayRun = 0
            try:
                tfiles = query.getFileList(camName, ffId)
                #print(tfiles)
                for tfile in tfiles:
                    
                    curFfId = tfile[0]
                    ffNumber = tfile[1]
                    curSkyId = tfile[2]
                    timgName = tfile[3] #G021_tom_objt_190109T13531492.fit
                    tpath = tfile[4] #/data3/G002_021_190109/G021_tom_objt_190109T13531492.fit
                    
                    imgDate = timgName[14:20]
                    pathDate = tpath[16:22]
                    if imgDate!=pathDate:
                        ffId=curFfId
                        startProcess = False
                        continue
                    elif not startProcess:
                        ffId=0
                        startProcess = True
                    
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
                        tdiff = BatchImageDiff(srcDir, dstDir, tools, camName, curSkyId)
                        tStr = "start diff: %s"%(timgName)
                        tdiff.log.info(tStr)
                        tdiff.sendMsg(tStr)
                        
                    if curFfId>ffId:
                        skyId=curSkyId
                        ffId=curFfId
                        
                        logfile0 = open(logfName0, 'a')
                        logfile0.write("\n\n%d\n"%(ffId))
                        logfile0.close()
                        
                        tpathfz = "%s.fz"%(tpath)
                        if os.path.exists(tpath) or os.path.exists(tpathfz):
                            starttime = datetime.now()
                            tdiff.processImg(srcDir, timgName, ffNumber)
                            endtime = datetime.now()
                            runTime = (endtime - starttime).seconds
                            tdiff.log.info("totalTime %d seconds, sky:%d, ffNum:%d, %s"%(runTime, curSkyId, ffNumber, timgName))
                        else:
                            print("%s not exist"%(tpath))
                #if curFfId>ffId:
                #    break
            except Exception as e:
                print(str(e))
                tstr = traceback.format_exc()
                print(tstr)
                try:
                    if 'tdiff' in locals():
                        tStr = "diff error"
                        tdiff.log.info(tStr)
                        tdiff.sendMsg(tStr)
                except Exception as e1:
                    print(str(e1))
                    tstr = traceback.format_exc()
                    print(tstr)
            if len(tfiles)==0:
                time.sleep(5)
            nigRun = nigRun+1
            #if nigRun>=1:
            #    break
        else:
            # day temp file clean
            try:
                if ('tdiff' in locals()) and (dayRun==0):
                     tdiff.initReg(0)
            except Exception as e1:
                print(str(e1))
                tstr = traceback.format_exc()
                print(tstr)
                
            nigRun = 0
            dayRun = dayRun+1
            skyId = 0
            ffId = 0
            startProcess = False
            
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
    
