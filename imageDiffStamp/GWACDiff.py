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
        
    def __init__(self, camName, dataDest, tools): 
        
        self.camName = camName
        self.tools = tools
        self.toolPath = tools.rootPath
        self.log = tools.log
        
        self.modelPath="%s/tools/mlmodel"%(self.toolPath)
        #self.modelName='model_128_5_RealFOT_8_190111.h5'
        #self.modelName='model_RealFOT_64_100_fot10w_20190122_dropout.h5'
        self.modelName='model_RealFOT_createModel_08_16_32_60_2.h5' #model_RealFOT_createModel_08_16_32_60_2.h5 model_80w_20190403_branch3_train12_79
        self.ot2Classifier = OT2Classify(self.toolPath, self.log, self.modelName)
        
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim"
        self.tmpUpload="/dev/shm/gwacupload"
        self.tmpCat="%s/tmp"%(self.tmpRoot)
        self.cmbCat="%s/cmbCat"%(self.tmpRoot)
        self.tmpAlign="%s/align"%(self.tmpRoot)
        self.diff="%s/diff"%(self.tmpRoot)
        self.makeDiffTmpl="%s/makeTmpl"%(self.tmpRoot)
        self.doDiffTmpl="%s/tmpl"%(self.tmpRoot)
        
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
            
            #if dtype=='cat':
            #    skyName, ra,dec = self.tools.removeHeaderAndOverScan(tmpCat,objectImg)
            #else:
            #    skyName, ra,dec = self.tools.getRaDec(tmpCat,objectImg)
            skyName, ra,dec = 'sky001', 0, 0
                
            #sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
            sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
            fpar='sex_diff.par'
            
            #objectImgCat, isSuccess = self.tools.runSextractor(objectImg, tmpCat, tmpCat, fpar, sexConf, cmdStatus=2)
            objectImgCat, isSuccess = self.tools.runSextractor(objectImg, tmpCat, tmpCat, fpar, sexConf)
            if os.path.exists("%s/%s"%(tmpCat, objectImgCat)):
                starNum, fwhmMean, fwhmRms, bgMean, bgRms = self.tools.basicStatistic(tmpCat, objectImgCat)
                if starNum>0 and fwhmMean>1.5:
                    isSuccess = True
                    os.system("cp %s/%s %s/%s.cat"%(tmpCat, objectImgCat, destDir, imgpre))
                    os.system("cp %s/%s_bkg.fit %s/%s.fit"%(tmpCat, objectImgCat.split('.')[0], destDir, imgpre))
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
                
        #skyName, ra,dec = self.tools.removeHeaderAndOverScan(self.tmpAlign,objectImg)
        skyName, ra,dec = 'sky001', 0, 0
        
        #if templateImg==imgName:
        
        os.system("cp %s/%s.cat %s/%s"%(self.catDir, imgpre, self.tmpAlign, objectCat))
        os.system("cp %s/%s.cat %s/%s"%(self.tmplAlignDir, templateImg.split(".")[0] , self.tmpAlign, ttmplCat))
        alignRst = doAll(self.tmpAlign, ttmplCat, self.tmpAlign, objectCat, self.tmpAlign, objectImg, self.alignDir, imgName, templateImg)
        if alignRst[0]>0:
            #print("totalMatchNum, xshift,yshift, xrotation, yrotation, blindStarNum, mchRatios")
            totalMatchNum, xshift,yshift, xrotation, yrotation, blindStarNum, mchRatios = alignRst
            print("alignImage: %s, xshift=%f,yshift=%f"%(imgName, xshift,yshift))
            self.log.info(alignRst)
            isSuccess = True
    
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** alignImage %s use %d seconds"%(imgName, runTime))
        return isSuccess
        
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
                
        os.system("cp %s/%s.fit %s/ti.fit"%(self.doDiffTmpl, tmplImgPre, self.diff))
        os.system("cp %s/%s.fit %s/oi.fit"%(self.alignDir, oImgPre, self.diff))
        
        objTmpResi, objTmpConv, runSuccess = self.tools.runHotpants('oi.fit', 'ti.fit', self.diff)
        if not runSuccess:
            self.log.error("diffImage failure: %s"%(imgName))
            return False
        
        os.system("cp %s/%s %s/%s_resi.fit"%(self.diff, objTmpResi, self.diffImgDir, oImgPre))
        os.system("cp %s/%s %s/%s_conv.fit"%(self.diff, objTmpConv, self.diffImgDir, oImgPre))
        
        ''' '''   
        tgrid = 1
        tsize = 800
        tzoom = 1
        timg = getThumbnail(self.diff, objTmpResi, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        #timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_resi.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
          
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** image diff total use %d seconds"%(runTime))
        
        return resultFlag
    
    def classifyAndUpload(self, imgName, tmplParms, runName, skyName):
                
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
        os.system("cp %s/%s %s/%s"%(self.cmbDir, imgName, upDir, imgName))
        #print("cp %s/%s %s/%s"%(ttmplPath, tmplImgName, upDir, tmplImgName))
        os.system("cp %s/%s %s/%s"%(ttmplPath, tmplImgName, upDir, tmplImgName))
        resiImg = "%s_resi.fit"%(oImgPre)
        #print("cp %s/%s %s/%s"%(self.diffImgDir, resiImg, upDir, resiImg))
        os.system("cp %s/%s %s/%s"%(self.diffImgDir, resiImg, upDir, resiImg))
        
        totImgsName = '%s_totimg.npz'%(oImgPre)
        fotImgsName = '%s_fotimg.npz'%(oImgPre)

        self.ot2Classifier.doClassifyAndUpload(self.destDir, totImgsName, fotImgsName, 
                          upDir, imgName, tmplImgName, resiImg, 
                          imgName, self.tools.serverIP, runName, skyName)
        