# -*- coding: utf-8 -*-
import scipy as S
import scipy.ndimage
import numpy as np
from astropy.io import fits
import os
import time
import math
import logging
import subprocess
import datetime
import matplotlib.pyplot as plt
from PIL import Image
import cv2
from skimage.morphology import square
from skimage.filters.rank import mean
from gwac_util import getThumbnail, getThumbnail_, zscale_image, genPSFView
from QueryData import QueryData

import astrotools as tools

class ImageDiff(object):
    def __init__(self): 
        
        self.verbose = True
        
        self.varDir = "%s/tools/simulate_tools"%(os.getcwd())
        self.matchProgram="%s/tools/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"%(os.getcwd())
        self.imgDiffProgram="%s/tools/hotpants/hotpants"%(os.getcwd())
        self.funpackProgram="%s/tools/cfitsio/funpack"%(os.getcwd())
        
        self.tmpRoot="/dev/shm/gwacsim"
        self.tmpDir="%s/tmp"
        self.tmpCat="%s/cat"
        self.templateDir="%s/tmpl"
        
        self.dataRoot = "/data/gwac_data"
        self.srcDir0 = "%s/gwac_orig_fits"%(self.dataRoot)
        self.srcDir = "%s/gwac_orig_fits/181209"%(self.dataRoot)
        self.destDir="%s/gwac_simot/data_1213/sample"%(self.dataRoot)
        self.preViewDir="%s/gwac_simot/data_1213/preview"%(self.dataRoot)
        self.origPreViewDir="%s/gwac_simot/data_1213/orig_preview"%(self.dataRoot)
        
        os.environ['VER_DIR'] = self.varDir
                
        if not os.path.exists(self.templateDir):
            os.system("mkdir -p %s"%(self.templateDir))
        if not os.path.exists(self.tmpDir):
            os.system("mkdir -p %s"%(self.tmpDir))
        if not os.path.exists(self.tmpCat):
            os.system("mkdir -p %s"%(self.tmpCat))
        if not os.path.exists(self.destDir):
            os.system("mkdir -p %s"%(self.destDir))
        if not os.path.exists(self.preViewDir):
            os.system("mkdir -p %s"%(self.preViewDir))
        if not os.path.exists(self.origPreViewDir):
            os.system("mkdir -p %s"%(self.origPreViewDir))
            
        self.objectImg = 'oi.fit'
        self.templateImg = 'ti.fit'
        self.objectImgSim = 'ois.fit'
        self.objTmpResi = 'otr.fit'
        self.simTmpResi = 'str.fit'
        
        self.objectImgSimAdd = 'oisa.cat'
        self.objectImgCat = 'oi.cat'
        self.templateImgCat = 'ti.cat'
        self.objectImgSimCat = 'ois.cat'
        self.objTmpResiCat = 'otr.cat'
        self.simTmpResiCat = 'str.cat'
                
        self.subImgSize = 21
        self.imgShape = []  
             
        self.selTemplateNum = 10
        self.imglist = []
        self.tmplImgName = ""
        self.tmplImgIdx = 0
        
        self.log = logging.getLogger() #create logger
        self.log.setLevel(logging.DEBUG) #set level of logger
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s") #set format of logger
        logging.Formatter.converter = time.gmtime #convert time in logger to UCT
        #filehandler = logging.FileHandler("%s/otSim.log"%(self.destDir), 'w+')
        filehandler = logging.FileHandler("%s/otSim.log"%(self.tmpDir), 'w+')
        filehandler.setFormatter(formatter) #add format to log file
        self.log.addHandler(filehandler) #link log file to logger
        if self.verbose:
            streamhandler = logging.StreamHandler() #create print to screen logging
            streamhandler.setFormatter(formatter) #add format to screen logging
            self.log.addHandler(streamhandler) #link logger to screen logging
    

    def diffImage(self, oImg, tImg):
        
        starttime = datetime.datetime.now()
        
        self.objectImgOrig = oImg
        self.templateImgOrig = tImg
    
        os.system("rm -rf %s/*"%(self.tmpDir))
        
        oImgfz = "%s/%s.fz"%(self.srcDir,oImg)
        tImgfz = "%s/%s.fz"%(self.srcDir,tImg)
        
        if (not os.path.exists(oImgfz)) or (not os.path.exists(tImgfz)):
            print("%s or %s not exist"%(oImgfz, tImgfz))
            return
                
        os.system("cp %s/%s.fz %s/%s.fz"%(self.srcDir, oImg, self.tmpDir, self.objectImg))
        os.system("cp %s/%s.fz %s/%s.fz"%(self.srcDir, tImg, self.tmpDir, self.templateImg))
        os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, self.objectImg))
        os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, self.templateImg))
        
        tools.removeHeaderAndOverScan(self, self.objectImg)
        tools.removeHeaderAndOverScan(self, self.templateImg)

        sexConf=['-DETECT_MINAREA','7','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff_fot.par'
        self.objectImgCat = tools.runSextractor(self, self.objectImg, fpar, sexConf)
        self.templateImgCat = tools.runSextractor(self, self.templateImg, fpar, sexConf)
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, self.objectImgCat))
        print("objImg extract star %d"%(tdata.shape[0]))
        if len(tdata.shape)<2 or tdata.shape[0]<5000:
            print("%s has too little stars, break this run"%(oImg))
            return
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, self.templateImgCat))
        print("tempImg extract star %d"%(tdata.shape[0]))
        if len(tdata.shape)<2 or tdata.shape[0]<5000:
            print("%s has too little stars, break this run"%(tImg))
            return
        
        badPixCat = tools.processBadPix(self)
        
        '''  '''
        mchFile, nmhFile = tools.runSelfMatch(self, self.objectImgCat, self.r16)
        self.osn16 = nmhFile
        mchFile, nmhFile = tools.runSelfMatch(self, self.templateImgCat, self.r16)
        self.tsn16 = nmhFile
        
        mchFile, nmhFile, mchPair = tools.runCrossMatch(self, self.osn16, self.tsn16, 10)
        osn16_tsn16_cm5 = mchFile
        osn16_tsn16_cm5_pair = mchPair
        
        tools.gridStatistic(self, osn16_tsn16_cm5, gridNum=4)
        
        newimage, h, xshift, yshift = tools.getMatchPos(self, self.osn16, self.tsn16, osn16_tsn16_cm5_pair)
        print("astrometry pos transform, xshift=%.2f, yshift=%.2f"%(xshift,yshift))
                
        newName = "new.fit"
        newPath = "%s/%s"%(self.tmpDir, newName)
        if os.path.exists(newPath):
            os.remove(newPath)
        hdu = fits.PrimaryHDU(newimage)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath)
        '''
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, self.objectImgCat))
        tdata = np.array([tdata])
        tdata2 = cv2.perspectiveTransform(tdata, h)
        tdata2 = tdata2[0]
                
        oiTransName = "%s_trans.cat"%(self.objectImgCat[:self.objectImgCat.index(".")])
        oiTransPath = "%s/%s"%(self.tmpDir, oiTransName)
        with open(oiTransPath, 'w') as fp1:
            for tobj in tdata2:
               fp1.write("%.3f %.3f\n"%(tobj[0], tobj[1]))
        '''
        self.objTmpResi = tools.runHotpants(self, newName, self.templateImg)
        
        tgrid = 4
        tsize = 1000
        tzoom = 1
        oImgPre = oImg[:oImg.index(".")]
        timg = getThumbnail(self.tmpDir, self.objTmpResi, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_resi.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        timg = getThumbnail(self.tmpDir, self.objectImg, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_obj.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        timg = getThumbnail(self.tmpDir, self.templateImg, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_tmp.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        
        fpar='sex_diff.par'
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        resiCat = tools.runSextractor(self, self.objTmpResi, fpar, sexConf)
        
        mchFile, nmhFile = tools.runSelfMatch(resiCat, 1)
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, resiCat))
        print("resi image star %d"%(tdata.shape[0]))
        
        mchRadius = 10
        mchFile, nmhFile, mchPair = tools.runCrossMatch(self, resiCat, self.templateImgCat, mchRadius)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
        print("resi star match template %d"%(tdata.shape[0]))
        
        mchFile, nmhFile, mchPair = tools.runCrossMatch(self, mchFile, badPixCat, 5)
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, nmhFile))
        print("resi star match template and remove badpix %d"%(tdata.shape[0]))
        
        size = self.subImgSize
        fSubImgs, fparms = tools.getWindowImgs(self, newName, self.templateImg, self.objTmpResi, tdata, size)
        
        
        oImgPre = oImg[:oImg.index(".")]
        fotpath = '%s/%s_otimg_fot.npz'%(self.destDir, oImgPre)
        np.savez_compressed(fotpath, fot=fSubImgs, parms=fparms)
        
        self.log.info("\n******************")
        self.log.info("simulation False OT, total sub image %d"%(len(fSubImgs)))
        
        resiImgs = []
        for timg in fSubImgs:
            resiImgs.append(timg[2])

        preViewPath = "%s/%s_psf.jpg"%(self.preViewDir, oImgPre)
        #if not os.path.exists(preViewPath):
        psfView = genPSFView(resiImgs)
        Image.fromarray(psfView).save(preViewPath)
                        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("image diff total use %d seconds"%(runTime))
        
    def makeTemplate(self):
        
        tImgNum = len(self.imglist)
        tparms = []
        for tIdx in range(tImgNum-self.selTemplateNum,tImgNum):
            tparms.append(self.imglist[tIdx])
            
        tparms = np.array(tparms)
        print(tparms)
        tfwhms = tparms[:,5]
        minIdx = np.argmin(tfwhms)
        
        self.tmplImgName = tparms[minIdx][0]
        self.tmplImgIdx = tImgNum-self.selTemplateNum + minIdx
        print("%d, %s has min fwhm %f"%(self.tmplImgIdx, self.tmplImgName, tparms[minIdx][5]))
        
        imgName = self.tmplImgName
        imgpre= imgName.split(".")[0]
        
        os.system("rm -rf %s/*"%(self.templateDir))
        os.system("cp %s/%s.fz %s/%s.fz"%(self.srcDir, imgName, self.templateDir, self.templateImg))
        os.system("%s %s/%s.fz"%(self.funpackProgram, self.templateDir, self.templateImg))
        
        tools.removeHeaderAndOverScan(self.templateImg, self.templateDir)
        sexConf=['-DETECT_MINAREA','7','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        tmplCat = tools.runSextractor(self.templateImg, self.templateDir, self.templateDir, self.varDir, fpar, sexConf, mdStatus=0)
        
        objName = 'ti.fit'
        bkgName = 'ti_bkg.fit'
        badPixCat = tools.processBadPix(objName, bkgName, self.templateDir, self.templateDir, self.varDir)
        
        #do astrometry, get wcs        
        
    
    def register(self, imgName):
        
        starttime = datetime.datetime.now()
        
        imgpre= imgName.split(".")[0]
        self.objectImgOrig = imgName
        os.system("rm -rf %s/*"%(self.tmpDir))
        oImgfz = "%s/%s.fz"%(self.srcDir,imgName)
        if not os.path.exists(oImgfz):
            print("%s not exist"%(oImgfz))
            return
                
        os.system("cp %s/%s.fz %s/%s.fz"%(self.srcDir, imgName, self.tmpDir, self.objectImg))
        os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, self.objectImg))
        
        tools.removeHeaderAndOverScan(self.objectImg, self.tmpDir)

        sexConf=['-DETECT_MINAREA','7','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        self.objectImgCat = tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, self.varDir, fpar, sexConf)
        mchFile16, nmhFile16 = tools.runSelfMatch(self, self.objectImgCat, 16)
        
        os.system("cp %s/%s %s/%s.cat"%(self.tmpDir, nmhFile16, self.tmpCat, imgpre))
                
        if len(self.imglist)==0:
            self.imglist.append((imgName, 0, 0, 0))
        else:
            timgCat = self.imglist[-1][0]
            mchFile, nmhFile, mchPair = tools.runCrossMatch(self, nmhFile16, timgCat, 10)
            osn16_tsn16_cm = mchFile
            osn16_tsn16_cm_pair = mchPair
            
            tNumMean, tNumMin, tNumRms = tools.gridStatistic(self, osn16_tsn16_cm, gridNum=4)
            fwhmMean, fwhmRms = tools.fwhmEvaluate(osn16_tsn16_cm)
            
            h, xshift, yshift, xrms, yrms = tools.getMatchPos(self, self.osn16, self.tsn16, osn16_tsn16_cm_pair)
            print("astrometry pos transform, xshift=%.2f, yshift=%.2f"%(xshift,yshift))
            
            self.imglist.append((imgName, xshift, yshift, xrms, yrms, fwhmMean))
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("image diff total use %d seconds"%(runTime))
    
        
    def batchSim(self):
        
        query = QueryData()
        filesNum = query.queryFilesNum()
        
        for tnum in filesNum:
            
            if tnum[3]>1000 and tnum[2]%5>0:
                files = query.getFileList(tnum[1], tnum[2], tnum[0])
                total = len(files)
                self.log.info(tnum)
                
                ccd = files[0][1]
                #G004_041
                tpath1 = "G0%s_%s"%(ccd[:2], ccd)
                self.srcDir="%s/%s/%s"%(self.srcDir0,tnum[0], tpath1)
                
                for i in range(total):
                    
                    objectImg = files[i][0]
                    self.register(objectImg)
                    if i>=self.selTemplateNum:
                        if self.tmplImgIdx==0:
                            self.makeTemplate()
                        self.diffImage()
                    
            break
                        
            
if __name__ == "__main__":
    
    otsim = OTSimulation()
    otsim.batchSim()
    #otsim.test()
    #otsim.simFOT2('obj', 'tmp')
    