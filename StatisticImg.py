# -*- coding: utf-8 -*-
import scipy as S
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from random import randint, random
import pandas as pd
import sys
import math
import os
import time
import logging
import subprocess
from gwac_util import zscale_image, selectTempOTs, filtOTs, filtByEllipticity, genFinalOTDs9Reg, genPSFView, getThumbnail
from imgSim import ImageSimulation
import scipy.ndimage
from PIL import Image


class StatisticImg(object):
    def __init__(self):
        
        self.verbose = True
        
        self.varDir = "/home/xy/Downloads/myresource/deep_data2/simulate_tools"
        self.srcDir = "/home/xy/Downloads/myresource/deep_data2/G180216" # ls CombZ_*fit
        self.catDir = "/home/xy/Downloads/myresource/deep_data2/G180216Cat"
        self.tmpDir="/run/shm/gwacsim"
        self.destDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0923"
        self.matchProgram="/home/xy/program/netbeans/C/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"
        self.imgDiffProgram="/home/xy/program/C/hotpants/hotpants"
                
        if not os.path.exists(self.tmpDir):
            os.system("mkdir %s"%(self.tmpDir))
        if not os.path.exists(self.destDir):
            os.system("mkdir %s"%(self.destDir))
        if not os.path.exists(self.catDir):
            os.system("mkdir %s"%(self.catDir))
            
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
        self.r5 = 5
        self.r10 = 10
        self.r16 = 16
        self.r24 = 24
        self.r32 = 32
        self.r46 = 46
        
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


    
    #source extract
    def runSextractor(self, fname, sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']):
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(self.tmpDir, self.objectImg)
        outFile = "%s.cat"%(outpre)
        outFPath = "%s/%s"%(self.catDir, outFile)
        cnfPath = "%s/config/OTsearch.sex"%(self.varDir)
        
        #DETECT_MINAREA   5              # minimum number of pixels above threshold
        #DETECT_THRESH    3.0             #  <sigmas>  or  <threshold>,<ZP>  in  mag.arcsec-2  
        #ANALYSIS_THRESH  3.0
        # run sextractor from the unix command line
        cmd = ['sex', fullPath, '-c', cnfPath, '-CATALOG_NAME', outFPath]
        cmd = cmd + sexConf
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        #self.log.info(stdoutstr)
        #self.log.info(stderrstr)
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run sextractor success.")
            self.log.debug("generate catalog %s"%(outFPath))
        else:
            self.log.error("sextractor failed.")
            
        return outFile

    
    def removeHeader(self, fname):
        
        fullPath = "%s/%s"%(self.tmpDir, fname)
        
        fname='G022_mon_objt_180226T17492514_2.fits'
        keyword=['WCSASTRM','WCSDIM','CTYPE1','CTYPE2',
                 'CRVAL1','CRVAL2','CRPIX1','CRPIX2',
                 'CD1_1','CD1_2','CD2_1','CD2_2','WAT0_001',
                 'WAT1_001','WAT1_002','WAT1_003','WAT1_004','WAT1_005','WAT1_006','WAT1_007','WAT1_008',
                 'WAT2_001','WAT2_002','WAT2_003','WAT2_004','WAT2_005','WAT2_006','WAT2_007','WAT2_008']
    
        with fits.open(fullPath, mode='update') as hdul:
            hdr = hdul[0].header
            for kw in keyword:
                hdr.remove(kw,ignore_missing=True)
            hdul.flush()
            hdul.close()
        
    def simImage(self, oImg):
    
        outpre= oImg.split(".")[0]
        os.system("rm -rf %s/*"%(self.tmpDir))
        os.system("cp %s/%s %s/%s"%(self.srcDir, oImg, self.tmpDir, self.objectImg))
        
        self.removeHeader(self.objectImg)
        self.objectImgCat = self.runSextractor(self.objectImg)
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r16)
        self.osn16 = nmhFile
        
        osn16s = selectTempOTs(self.osn16, self.tmpDir)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, osn16s))
        if len(tdata.shape)<2 or tdata.shape[0]<100:
            print("%s has too little stars, break this run"%(oImg))
            return
        osn16sf = filtOTs(osn16s, self.tmpDir)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, osn16sf))
        if len(tdata.shape)<2 or tdata.shape[0]<45:
            print("%s has too little stars, break this run"%(oImg))
            return
        
        imgSimClass = ImageSimulation()
        otImgs = imgSimClass.getTmpOtImgs(osn16sf, self.objectImg)
        
        psfView = genPSFView(otImgs)
        thumbnail = getThumbnail(self.srcDir, oImg, stampSize=(100,100), grid=(5, 5), innerSpace = 1)
        thumbnail = scipy.ndimage.zoom(thumbnail, 4, order=0)
        '''
        plt.clf()
        plt.figure(figsize=(20,20))
        plt.imshow(psfView, interpolation = "nearest", cmap='gray')
        plt.show()
        plt.clf()
        plt.figure(figsize=(20,20))
        plt.imshow(thumbnail, interpolation = "nearest", cmap='gray')
        plt.show()
        '''
        tpath11 = "%s_view"%(self.srcDir)
        if not os.path.exists(tpath11):
            os.system("mkdir %s"%(tpath11))
        dpath1 = "%s/%s_psf.jpg"%(tpath11, outpre)
        dpath2 = "%s/%s_thb.jpg"%(tpath11, outpre)
        Image.fromarray(psfView).save(dpath1)
        Image.fromarray(thumbnail).save(dpath2)
        
    def batchSim(self):
            
        # ls CombZ_*fit
        templateImg = 'CombZ_temp.fit'
        flist = os.listdir(self.srcDir)
        flist.sort()
        
        imgs = []
        for tfilename in flist:
            if tfilename.find("fit")>-1:
                imgs.append(tfilename)
                
        for i, timg in enumerate(imgs):
            print("\n\nprocess %s"%(timg))
            os.system("rm -rf %s/*"%(self.tmpDir))
            os.system("cp %s/%s %s/%s"%(self.srcDir, timg, self.tmpDir, self.objectImg))
            
            self.removeHeader(self.objectImg)
            self.objectImgCat = self.runSextractor(timg)
            break

        
if __name__ == "__main__":
    
    otsim = StatisticImg()
    otsim.batchSim()
    #otsim.testSimImage()
    #otsim.simFOT2('obj', 'tmp')
    