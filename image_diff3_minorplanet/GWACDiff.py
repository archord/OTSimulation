# -*- coding: utf-8 -*-
import numpy as np
import os
import sys
import math
import time
import scipy
import scipy.ndimage
from datetime import datetime
import traceback
from astropy.io import fits
from PIL import Image
from gwac_util import getThumbnail, genPSFView, getWindowImgs, getLastLine
from QueryData import QueryData
from astropy.wcs import WCS

from astrotools import AstroTools
#from ot2classify import OT2Classify
from blindmatch import doAll
from QueryMinorPlanet import QueryMinorPlanet

            
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
        
    def __init__(self, camName, dataDest, tools): 
        
        self.camName = camName
        self.tools = tools
        self.toolPath = tools.rootPath
        self.log = tools.log
        
        self.modelPath="%s/tools/mlmodel"%(self.toolPath)
        #self.modelName='model_128_5_RealFOT_8_190111.h5'
        #self.modelName='model_RealFOT_64_100_fot10w_20190122_dropout.h5'
        self.modelName='model_RealFOT_createModel_08_16_32_60_2.h5' #model_RealFOT_createModel_08_16_32_60_2.h5 model_80w_20190403_branch3_train12_79
        #self.ot2Classifier = OT2Classify(self.toolPath, self.log, self.modelName)
        
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim"
        self.tmpUpload="/dev/shm/gwacupload"
        self.tmpCat="%s/tmp"%(self.tmpRoot)
        self.cmbCat="%s/cmbCat"%(self.tmpRoot)
        self.tmpAlign="%s/align"%(self.tmpRoot)
        self.diff="%s/diff"%(self.tmpRoot)
        self.makeDiffTmpl="%s/makeTmpl"%(self.tmpRoot)
        self.doDiffTmpl="%s/tmpl"%(self.tmpRoot)
        self.tmpAstro="%s/astro"%(self.tmpRoot)
        
        self.reInitDataDir(dataDest)

    def sendMsg(self, tmsg):
        
        tmsgStr = "%s\n %s"%(self.camName, tmsg)
        self.tools.sendTriggerMsg(tmsgStr)
    
    def reInitDataDir(self, dataDest):
        
        if not os.path.exists(self.tmpRoot):
            os.system("mkdir -p %s"%(self.tmpRoot))
        if not os.path.exists(self.tmpUpload):
            os.system("mkdir -p %s"%(self.tmpUpload))
                
        os.system("rm -rf %s/*"%(self.tmpRoot))
        os.system("rm -rf %s/*"%(self.tmpUpload))
        
        if not os.path.exists(self.makeDiffTmpl):
            os.system("mkdir -p %s"%(self.makeDiffTmpl))
        if not os.path.exists(self.tmpCat):
            os.system("mkdir -p %s"%(self.tmpCat))
        if not os.path.exists(self.cmbCat):
            os.system("mkdir -p %s"%(self.cmbCat))
        if not os.path.exists(self.diff):
            os.system("mkdir -p %s"%(self.diff))
        if not os.path.exists(self.tmpAlign):
            os.system("mkdir -p %s"%(self.tmpAlign))
        if not os.path.exists(self.doDiffTmpl):
            os.system("mkdir -p %s"%(self.doDiffTmpl))
        if not os.path.exists(self.tmpAstro):
            os.system("mkdir -p %s"%(self.tmpAstro))
        
        self.catDir="%s/A_cat"%(dataDest)
        self.tmplAlignDir="%s/B_template_align"%(dataDest)
        self.alignDir="%s/C_align"%(dataDest)
        self.cmbDir="%s/D_combine5"%(dataDest)
        self.cmbCatDir="%s/E_combine5Cat"%(dataDest)
        self.tmplDiffDir="%s/F_template_diff"%(dataDest)
        self.diffImgDir="%s/G_diffImg"%(dataDest)
        self.diffCatDir="%s/H_diffCat"%(dataDest)
        self.origPreViewDir="%s/I_origPreview"%(dataDest)
        self.destDir = "%s/J_subImg"%(dataDest)
        self.subImgViewDir = "%s/J_subImgPreview"%(dataDest)
            
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
        if not os.path.exists(self.destDir):
            os.system("mkdir -p %s"%(self.destDir))
        if not os.path.exists(self.subImgViewDir):
            os.system("mkdir -p %s"%(self.subImgViewDir))
                
        
    def getCat(self, srcDir, imgName, destDir, dtype='cat'):
        
        starttime = datetime.now()
        
        try:
            if dtype=='cat':
                tmpCat=self.tmpCat
            elif dtype=='cmb':
                tmpCat=self.cmbCat
                
            isSuccess = False
            imgpre= imgName.split(".")[0]
            os.system("rm -rf %s/*"%(tmpCat))
            objectImg = 'oi.fit'
            
            oImgf = "%s/%s.fit"%(srcDir,imgpre)
            oImgfz = "%s/%s.fit.fz"%(srcDir,imgpre)
            if os.path.exists(oImgf):
                os.system("cp %s/%s.fit %s/%s"%(srcDir, imgpre, tmpCat, objectImg))
            elif os.path.exists(oImgfz):
                os.system("cp %s/%s.fit.fz %s/%s.fz"%(srcDir, imgpre, tmpCat, objectImg))
                os.system("%s %s/%s.fz"%(self.funpackProgram, tmpCat, objectImg))
            else:
                self.log.warning("%s not exist"%(oImgf))
                return False, 0, 0, 0, 0
            
            if dtype=='cat':
                skyName, ra,dec = self.tools.removeHeaderAndOverScan(tmpCat,objectImg)
            else:
                skyName, ra,dec = self.tools.getRaDec(tmpCat,objectImg)
                
            #sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
            sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
            fpar='sex_diff.par'
            
            objectImgCat, isSuccess = self.tools.runSextractor(objectImg, tmpCat, tmpCat, fpar, sexConf)
            if os.path.exists("%s/%s"%(tmpCat, objectImgCat)):
                starNum, fwhmMean, fwhmRms, bgMean, bgRms = self.tools.basicStatistic(tmpCat, objectImgCat)
                if starNum>0 and fwhmMean>1.5:
                    isSuccess = True
                    os.system("cp %s/%s %s/%s.cat"%(tmpCat, objectImgCat, destDir, imgpre))
                else:
                    isSuccess = False
            else:
                isSuccess = False
                starNum, fwhmMean, fwhmRms, bgMean, bgRms = 0,0,0,0,0
            
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            self.log.info("********** getCat %s use %d seconds"%(imgName, runTime))
            return isSuccess, skyName, starNum, fwhmMean, bgMean
    
        except Exception as e:
            tstr = traceback.format_exc()
            self.log.error(tstr)
            self.log.error(tstr)
                    
        return False, 0, 0, 0, 0
    
    def getAlignTemplate(self, tmplParms, skyName):
        
        starttime = datetime.now()
        tmplRoot = '/data/gwac_data/gwac_wcs_idx'
        status = tmplParms[0]
        files = tmplParms[1]
        imgName = ''
        if status=='2': #no history template, select template from current observed image
            imgName = files[0][0]
            imgpre = imgName.split(".")[0]
            os.system("cp %s/%s.cat %s/%s.cat"%(self.catDir, imgpre, self.tmplAlignDir, imgpre))
        elif status=='1':
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
        
        #if templateImg==imgName:
        
        os.system("cp %s/%s.cat %s/%s"%(self.catDir, imgpre, self.tmpAlign, objectCat))
        os.system("cp %s/%s.cat %s/%s"%(self.tmplAlignDir, templateImg.split(".")[0] , self.tmpAlign, ttmplCat))
        alignRst = doAll(self.tmpAlign, ttmplCat, self.tmpAlign, objectCat, self.tmpAlign, objectImg, self.alignDir, imgName, templateImg)
        
        alignImgName = "%s_align.fit"%(imgpre)
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        fpar='sex_diff.par'
        self.tools.runSextractor(alignImgName, self.alignDir, self.alignDir, fpar, sexConf)
        
        t2oX, t2oY=[],[]
        if alignRst[0]>0:
            #print("totalMatchNum, xshift,yshift, xrotation, yrotation, blindStarNum, mchRatios")
            totalMatchNum, xshift,yshift, xrotation, yrotation, blindStarNum, mchRatios, \
            oiStarJoinNum,tiStarJoinNum, otMchNum, xshift2,yshift2, xrms2, yrms2, t2oX, t2oY= alignRst
            print("alignImage: %s, xshift=%f,yshift=%f"%(imgName, xshift,yshift))
            alignRst = alignRst[:-2].copy()
            alignRst.append(imgName)
            alignRst.append(templateImg)
            alignRst.append('imageAlignParmsForDebug')
            self.log.info(alignRst)
            if mchRatios>80.0:
                isSuccess = True
    
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** alignImage %s use %d seconds"%(imgName, runTime))
        return isSuccess, t2oX, t2oY
        
    def superCombine(self, imgNames, regions=[2,2]):

        try:
            starttime = datetime.now()
            
            tpath01="%s/%s_align.fit"%(self.alignDir, imgNames[0].split('.')[0])
            theader = fits.getheader(tpath01)
            for j in range(len(imgNames)):
                theader['IMG%03d'%(j)]=imgNames[j]
            
            tCmbImg = np.array([])
            regWid = 0
            regHei = 0
            for ty in range(regions[0]):
                for tx in range(regions[1]):
                    imgs = []
                    for j in range(len(imgNames)):
                        tname = imgNames[j]
                        tpath00="%s/%s_align.fit"%(self.alignDir, tname.split('.')[0])
                        tdata1 = fits.getdata(tpath00,ext=0) #first image is template
                        if tCmbImg.shape[0]==0:
                            tCmbImg=np.zeros(tdata1.shape, dtype=np.uint16)
                            regWid = int(tCmbImg.shape[1]/2)
                            regHei = int(tCmbImg.shape[0]/2)
                        imgs.append(tdata1[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid].copy())

                    imgArray = np.array(imgs)
                    tCmbImg[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid] = np.median(imgArray,axis=0)
            
            #tCmbImg = tCmbImg.astype(np.uint16)
            outImgName = "%s_c%03d.fit"%(imgNames[0].split('.')[0], len(imgNames))
            #print("superCombine: get %s"%(outImgName))
            fits.writeto("%s/%s"%(self.cmbDir, outImgName), tCmbImg, header=theader,overwrite=True)
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            self.log.info("********** superCombine use %d seconds"%(runTime))
            
        except Exception as e:
            outImgName = ''
            self.log.error(str(e))
            tstr = traceback.format_exc()
            self.log.error(tstr)
        return outImgName
            
    def getImgCenter(self, tpath, imgName):
        
        starttime = datetime.now()
        
        try:
            starttime = datetime.now()
            
            os.system("rm -rf %s/*"%(self.tmpAstro))
            
            imgpre= imgName.split(".")[0]
            oImgf = "%s/%s.fit"%(tpath,imgpre)
            oImgfz = "%s/%s.fit.fz"%(tpath,imgpre)
            if os.path.exists(oImgf):
                os.system("cp %s/%s.fit %s/%s"%(tpath, imgpre, self.tmpAstro, self.templateImg))
            elif os.path.exists(oImgfz):
                os.system("cp %s/%s.fit.fz %s/%s.fz"%(tpath, imgpre, self.tmpAstro, self.templateImg))
                os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpAstro, self.templateImg))
            else:
                self.log.warning("%s not exist"%(oImgf))
                return False, 0, 0
            
            #tcmd = "cp %s/%s %s/%s"%(tpath, imgName, self.tmpAstro, self.templateImg)
            #self.log.info(tcmd)
            #os.system(tcmd)
            
            fieldId, ra,dec = self.tools.getRaDec(self.tmpAstro, self.templateImg)
            fpar='sex_diff.par'
            sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','7','-ANALYSIS_THRESH','7','-CATALOG_TYPE', 'FITS_LDAC']
            tmplCat, isSuccess = self.tools.runSextractor(self.templateImg, self.tmpAstro, self.tmpAstro, fpar, sexConf, outSuffix='_ldac.fit')
            if not isSuccess:
                self.log.error("getDiffTemplate runSextractor failure2")
                return isSuccess, 0,0
            
            self.tools.ldac2fits('%s/%s'%(self.tmpAstro,tmplCat), '%s/ti_cat.fit'%(self.tmpAstro))
            
            runSuccess = self.tools.runWCS(self.tmpAstro,'ti_cat.fit', ra, dec)
            
            ra_center, dec_center = ra,dec
            if runSuccess:
                wcs = WCS('%s/ti_cat.wcs'%(self.tmpAstro))
                ra_center, dec_center = wcs.all_pix2world(self.imgSize[1]/2, self.imgSize[0]/2, 1)
                tstr = 'read_ra_dec:(%.5f, %.5f), real_dec_center:(%.5f, %.5f)'%(ra, dec, ra_center, dec_center)
                self.log.info(tstr)
                #print(tstr)
            else:
                tstr = 'make template %s, get wcs error'%(self.origTmplImgName)
                self.log.error(tstr)
                #print(tstr)
            
            os.system("rm -rf %s/*"%(self.tmpAstro))
            
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            self.log.info("********** getImgCenter %s/%s use %d seconds"%(tpath, imgName, runTime))
            
        except Exception as e:
            runSuccess = False
            self.log.error(e)
            tstr = traceback.format_exc()
            self.log.error(tstr)
        
        return runSuccess, ra_center, dec_center
    
    def getDiffTemplate(self, tmplParms, skyName, alignCatParms):
        
        starttime = datetime.now()
        files = tmplParms[1]
        tmplImageName = files[-1][0]
        
        try:
            starttime = datetime.now()
            
            os.system("rm -rf %s/*"%(self.makeDiffTmpl))
            tmsgStr = "%s, select %s as template, it has fwhm %s, starNum %s, bg %s"%(skyName, tmplImageName, alignCatParms[5], alignCatParms[3], alignCatParms[6])
            #print(tmsgStr)
            self.log.info(tmsgStr)
            #self.sendMsg(tmsgStr)
    
            tcmd = "cp %s/%s %s/%s"%(self.cmbDir, tmplImageName, self.makeDiffTmpl, self.templateImg)
            self.log.info(tcmd)
            #print(tcmd)
            os.system(tcmd)
            
            fieldId, ra,dec = self.tools.getRaDec(self.makeDiffTmpl, self.templateImg)
            sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
            fpar='sex_diff.par'
            tmplCat, isSuccess = self.tools.runSextractor(self.templateImg, self.makeDiffTmpl, self.makeDiffTmpl, fpar, sexConf, cmdStatus=0)
            if not isSuccess:
                self.log.error("getDiffTemplate runSextractor failure1")
                return isSuccess
            
            sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5','-CATALOG_TYPE', 'FITS_LDAC']
            tmplCat, isSuccess = self.tools.runSextractor(self.templateImg, self.makeDiffTmpl, self.makeDiffTmpl, fpar, sexConf, cmdStatus=0, outSuffix='_ldac.fit')
            if not isSuccess:
                self.log.error("getDiffTemplate runSextractor failure2")
                return isSuccess
            
            self.tools.ldac2fits('%s/%s'%(self.makeDiffTmpl,tmplCat), '%s/ti_cat.fit'%(self.makeDiffTmpl))
            
            #tpath = "%s/%s"%(self.makeDiffTmpl,tmplCat)
            runSuccess = self.tools.runWCS(self.makeDiffTmpl,'ti_cat.fit', ra, dec)
            #ccdName = self.origTmplImgName[:4]
            #runSuccess = self.tools.runWCSRemotePC780(self.makeDiffTmpl,'ti_cat.fit', ra, dec, ccdName)
            
            if runSuccess:
                wcs = WCS('%s/ti_cat.wcs'%(self.makeDiffTmpl))
                ra_center, dec_center = wcs.all_pix2world(self.imgSize[1]/2, self.imgSize[0]/2, 1)
                self.log.info('read_ra_dec:(%.5f, %.5f), real_dec_center:(%.5f, %.5f)'%(ra, dec, ra_center, dec_center))
            else:
                self.log.error('make template %s, get wcs error'%(self.origTmplImgName))
            
            objName = 'ti.fit'
            bkgName = 'ti_bkg.fit'
            badPixCat = self.tools.processBadPix(objName, bkgName, self.makeDiffTmpl, self.makeDiffTmpl)
            
            imgPre= tmplImageName.split(".")[0]
            
            fitImg = "%s/%s"%(self.makeDiffTmpl, self.templateImg)
            cat = "%s/ti.cat"%(self.makeDiffTmpl)
            catFit = "%s/ti_cat.fit"%(self.makeDiffTmpl)
            wcsFile = '%s/ti_cat.wcs'%(self.makeDiffTmpl)
            badPix = '%s/%s'%(self.makeDiffTmpl, badPixCat)
            
            os.system("cp %s %s/%s.fit"%(fitImg, self.tmplDiffDir, imgPre))
            os.system("cp %s %s/%s.cat"%(cat, self.tmplDiffDir, imgPre))
            os.system("cp %s %s/%s_cat.fit"%(catFit, self.tmplDiffDir, imgPre))
            os.system("cp %s %s/%s.wcs"%(wcsFile, self.tmplDiffDir, imgPre))
            os.system("cp %s %s/%s_badpix.cat"%(badPix, self.tmplDiffDir, imgPre)) 
            
            os.system("rm -rf %s/*"%(self.makeDiffTmpl))
            
            endtime = datetime.now()
            runTime = (endtime - starttime).seconds
            self.log.info("********** getDiffTemplate %s use %d seconds"%(tmplImageName, runTime))
            
        except Exception as e:
            runSuccess = False
            self.log.error(e)
            tstr = traceback.format_exc()
            self.log.error(tstr)
            tmsgStr = "make template error"
            #self.sendMsg(tmsgStr)
        
        return runSuccess
        
    def diffImage(self, imgName, tmplParms):
        
        starttime = datetime.now()
        
        resultFlag = True
        oImgPre = imgName.split(".")[0]
        dateStr = imgName.split('_')[3][:6]
        
        os.system("rm -rf %s/*"%(self.diff))
        
        status = tmplParms[0]
        #tmplImgName = tmplParms[1][-1][0]
        tmplImgName = tmplParms[1][0][0]
        tmplImgPre = tmplImgName.split(".")[0]
        if status=='1':
            ttmplPath = self.tmplAlignDir
        else:
            ttmplPath = self.tmplDiffDir
        
        ofitPath = "%s/%s.fit"%(self.doDiffTmpl, tmplImgPre)
        if not os.path.exists(ofitPath):
            os.system("rm -rf %s/*"%(self.doDiffTmpl))
            os.system("cp %s/%s.fit %s/%s.fit"%(ttmplPath, tmplImgPre, self.doDiffTmpl, tmplImgPre))
            os.system("cp %s/%s.cat %s/%s.cat"%(ttmplPath, tmplImgPre, self.doDiffTmpl, tmplImgPre))
            os.system("cp %s/%s_badpix.cat %s/%s_badpix.cat"%(ttmplPath, tmplImgPre, self.doDiffTmpl, tmplImgPre))
                
        os.system("cp %s/%s.fit %s/ti.fit"%(self.doDiffTmpl, tmplImgPre, self.diff))
        os.system("cp %s/%s.cat %s/ti.cat"%(self.doDiffTmpl, tmplImgPre, self.diff))
        os.system("cp %s/%s_badpix.cat %s/ti_badpix.cat"%(self.doDiffTmpl, tmplImgPre, self.diff))
        
        os.system("cp %s/%s_align.fit %s/oi.fit"%(self.alignDir, oImgPre, self.diff))
        os.system("cp %s/%s_align.cat %s/oi.cat"%(self.alignDir, oImgPre, self.diff))
        
        theader = fits.getheader("%s/oi.fit"%(self.diff))
        dateObs = theader['DATE-OBS']
        timeObs = theader['TIME-OBS']
        dtStr = "%sT%s"%(dateObs, timeObs)
        
        objTmpResi, runSuccess = self.tools.runHotpants('oi.fit', 'ti.fit', self.diff)
        if not runSuccess:
            self.log.error("diffImage failure: %s"%(imgName))
            return False
        
        fpar='sex_diff.par'
        #sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        resiCat, isSuccess = self.tools.runSextractor(objTmpResi, self.diff, self.diff, fpar, sexConf)
        if not isSuccess:
            self.log.error("diffImage runSextractor failure")
            return isSuccess
            
        os.system("cp %s/%s %s/%s_resi.fit"%(self.diff, objTmpResi, self.diffImgDir, oImgPre))
        os.system("cp %s/%s %s/%s_resi.cat"%(self.diff, resiCat, self.diffCatDir, oImgPre))
        
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.diff, resiCat, 'oi.cat', 1) #1 and 5 
        
        badPix2Path = "%s/%s"%(self.diff, nmhFile)
        if os.path.exists(badPix2Path):
            badPixProps2 = np.loadtxt(badPix2Path)
        else:
            badPixProps2 = np.array([])

        mchRadius = 3 #15 10
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.diff, mchFile, 'ti.cat', mchRadius)
        
        fotPath = "%s/%s"%(self.diff, mchFile)
        if os.path.exists(fotPath):
            fotProps = np.loadtxt(fotPath)
        else:
            fotProps = np.array([])
        
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.diff, nmhFile, 'ti_badpix.cat', 1) #1 and 5 
        os.system("cp %s/%s %s/%s_tot.cat"%(self.diff, nmhFile, self.diffCatDir, oImgPre))
        
        totPath = "%s/%s"%(self.diff, nmhFile)
        if os.path.exists(totPath):
            totProps = np.loadtxt(totPath)
        else:
            totProps = np.array([])
        
        badPixPath = "%s/ti_badpix.cat"%(self.diff)
        if os.path.exists(badPixPath):
            badPixProps = np.loadtxt(badPixPath)
        else:
            badPixProps = np.array([])
            
        #badPixProps = np.array([])
        tstr = "orgBadPix %d, nmBad %d, match %d, noMatch %d"%(badPixProps.shape[0], badPixProps2.shape[0], fotProps.shape[0], totProps.shape[0])
        self.log.info(tstr)
        print(tstr)
        
        #size = self.subImgSize
        size = 68
        if totProps.shape[0]<500 and totProps.shape[0]>0:
            
            wcsPath = "%s/%s.wcs"%(ttmplPath, tmplImgPre)
            wcs = WCS(wcsPath)
        
            totSubImgs, totParms = getWindowImgs(self.diff, 'oi.fit', 'ti.fit', objTmpResi, totProps, size)
            if totParms.shape[0]>0:
                tXY = totParms[:,0:2]
                #tdates = np.repeat(dtStr,tXY.shape[0]).reshape((tXY.shape[0],1))
                tRaDec = wcs.all_pix2world(tXY, 1)
                totParms = np.concatenate((totParms, tRaDec), axis=1)
                
                searchRadius=0.05
                mpQuery = QueryMinorPlanet()
                mpQuery.connDb()
                mchDis = []
                for tpos in tRaDec:
                    ra = tpos[0]
                    dec = tpos[1]
                    tdis, tmag = mpQuery.matchMP(ra, dec, dateStr, dtStr, searchRadius+0.001)
                    mchDis.append([tdis,tmag])
                mpQuery.closeDb()
                    
                mchDis = np.array(mchDis)
                totParms = np.concatenate((totParms, mchDis), axis=1)
                
                totSubImgs1 = totSubImgs[mchDis[:,0]>=searchRadius]
                totParms1 = totParms[mchDis[:,0]>=searchRadius]
                mpSubImgs1 = totSubImgs[mchDis[:,0]<searchRadius]
                mpParms1 = totParms[mchDis[:,0]<searchRadius]
                
                tstr0 = "%s has %d tot, contain %d minorplanet."%(imgName, totParms.shape[0], mpParms1.shape[0])
                print(tstr0)
                self.log.info(tstr0)
                
                totpath = '%s/%s_totimg.npz'%(self.destDir, oImgPre)
                np.savez_compressed(totpath, imgs=totSubImgs1, parms=totParms1, obsUtc=dtStr)
                totpath = '%s/%s_mpimg.npz'%(self.destDir, oImgPre)
                np.savez_compressed(totpath, imgs=mpSubImgs1, parms=mpParms1, obsUtc=dtStr)
                
                if totSubImgs1.shape[0]>0:
                    resiImgs = []
                    for timg in totSubImgs1:
                        resiImgs.append(timg[2])
            
                    preViewPath = "%s/%s_tot.jpg"%(self.subImgViewDir, oImgPre)
                    #if not os.path.exists(preViewPath):
                    psfView = genPSFView(resiImgs)
                    Image.fromarray(psfView).save(preViewPath)
                
                if mpSubImgs1.shape[0]>0:
                    resiImgs = []
                    for timg in mpSubImgs1:
                        resiImgs.append(timg[2])
                    preViewPath = "%s/%s_mp.jpg"%(self.subImgViewDir, oImgPre)
                    #if not os.path.exists(preViewPath):
                    psfView = genPSFView(mpSubImgs1)
                    Image.fromarray(psfView).save(preViewPath)
            
            if fotProps.shape[0]>0 and fotProps.shape[0]<3000:
                fotSubImgs, fotParms = getWindowImgs(self.diff, 'oi.fit', 'ti.fit', objTmpResi, fotProps, size)
                if fotParms.shape[0]>0:
                    tXY = fotParms[:,0:2]
                    #tdates = np.repeat(dtStr,tXY.shape[0]).reshape((tXY.shape[0],1))
                    tRaDec = wcs.all_pix2world(tXY, 1)
                    fotParms = np.concatenate((fotParms, tRaDec), axis=1)
                    fotpath = '%s/%s_fotimg.npz'%(self.destDir, oImgPre)
                    np.savez_compressed(fotpath, imgs=fotSubImgs, parms=fotParms, obsUtc=dtStr)

            resultFlag = True
        else:
            tmsgStr = "%s.fit resi image has %d tot objects, maybe wrong"%(oImgPre, totProps.shape[0])
            self.log.error(tmsgStr)
            #self.sendMsg(tmsgStr)
            resultFlag = False
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** image diff total use %d seconds"%(runTime))
        
        return resultFlag
    
    def classifyAndUpload(self, imgName, tmplParms, runName, skyName, tcatParm):
                
        #os.system("rm -rf %s/*"%(self.diff))
        
        oImgPre = imgName.split(".")[0]
        status = tmplParms[0]
        #tmplImgName = tmplParms[1][-1][0]
        tmplImgName = tmplParms[1][0][0]
        if status=='1':
            ttmplPath = self.tmplAlignDir
        else:
            ttmplPath = self.tmplDiffDir
        
        upDir = "%s/%s"%(self.tmpUpload, oImgPre)
        tstr = "classifyAndUpload %s"%(upDir)
        self.log.info(tstr)
        print(tstr)
        if not os.path.exists(upDir):
            os.system("mkdir -p %s"%(upDir))
        
        #print("cp %s/%s %s/%s"%(self.cmbDir, imgName, upDir, imgName))
        os.system("cp %s/%s %s/%s"%(self.alignDir, imgName, upDir, imgName))
        #print("cp %s/%s %s/%s"%(ttmplPath, tmplImgName, upDir, tmplImgName))
        os.system("cp %s/%s %s/%s"%(ttmplPath, tmplImgName, upDir, tmplImgName))
        resiImg = "%s_resi.fit"%(oImgPre)
        #print("cp %s/%s %s/%s"%(self.diffImgDir, resiImg, upDir, resiImg))
        os.system("cp %s/%s %s/%s"%(self.diffImgDir, resiImg, upDir, resiImg))
        
        totImgsName = '%s_totimg.npz'%(oImgPre)
        fotImgsName = '%s_fotimg.npz'%(oImgPre)

        #self.ot2Classifier.doClassifyAndUpload(self.destDir, totImgsName, fotImgsName, 
        #                  upDir, imgName, tmplImgName, resiImg, 
        #                  imgName, self.tools.serverIP, runName, skyName, tcatParm)
        