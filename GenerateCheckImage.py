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


class GenerateCheckImage(object):
    def __init__(self):
        
        self.verbose = True
        
        self.varDir = "/home/xy/Downloads/myresource/deep_data2/simulate_tools"
        self.srcDir = "/home/xy/Downloads/myresource/deep_data2/chaodata" # ls CombZ_*fit
        self.tmpDir="/run/shm/gwacsim"
        self.destDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0923"
        self.matchProgram="/home/xy/program/netbeans/C/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"
        self.imgDiffProgram="/home/xy/program/C/hotpants/hotpants"
                
        if not os.path.exists(self.tmpDir):
            os.system("mkdir %s"%(self.tmpDir))
        if not os.path.exists(self.destDir):
            os.system("mkdir %s"%(self.destDir))
            
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
    
    #catalog self match
    def runSelfMatch(self, fname, mchRadius):
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(self.tmpDir, fname)
        
        # run sextractor from the unix command line
        cmd = [self.matchProgram, fullPath, str(mchRadius), '4', '5', '39']
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        mchFile = "%s_sm%d.cat"%(outpre,mchRadius)
        nmhFile = "%s_sn%d.cat"%(outpre,mchRadius)
        mchFilePath = "%s/%s"%(self.tmpDir,mchFile)
        nmhFilePath = "%s/%s"%(self.tmpDir,nmhFile)
        if os.path.exists(mchFilePath) and os.path.exists(nmhFilePath) and status==0:
            self.log.debug("run self match success.")
            self.log.debug("generate matched file %s"%(mchFile))
            self.log.debug("generate not matched file %s"%(nmhFile))
        else:
            self.log.error("self match failed.")
        
        return mchFile, nmhFile
    
    #crossmatch 
    def runCrossMatch(self, objCat, tmpCat, mchRadius):
        
        objpre= objCat.split(".")[0]
        tmppre= tmpCat.split(".")[0]
        objFPath = "%s/%s"%(self.tmpDir, objCat)
        tmpFPath = "%s/%s"%(self.tmpDir, tmpCat)
        outFPath = "%s/%s_%s.out"%(self.tmpDir, objpre,tmppre)
        
        # run sextractor from the unix command line
        cmd = [self.matchProgram, tmpFPath, objFPath, outFPath, str(mchRadius), '4', '5', '39']
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        mchPair = "%s_%s_cm%d.pair"%(objpre,tmppre,mchRadius)
        mchFile = "%s_%s_cm%d.cat"%(objpre,tmppre,mchRadius)
        nmhFile = "%s_%s_cn%d.cat"%(objpre,tmppre,mchRadius)
        mchPairPath = "%s/%s"%(self.tmpDir,mchPair)
        mchFilePath = "%s/%s"%(self.tmpDir,mchFile)
        nmhFilePath = "%s/%s"%(self.tmpDir,nmhFile)
        if os.path.exists(mchPairPath) and os.path.exists(mchFilePath) and os.path.exists(nmhFilePath) and status==0:
            self.log.debug("run catalog match success.")
            self.log.debug("generate pair file %s"%(mchPair))
            self.log.debug("generate matched file %s"%(mchFile))
            self.log.debug("generate not matched file %s"%(nmhFile))
        else:
            self.log.error("cross match failed.")
        
        return mchFile, nmhFile, mchPair
    
    #source extract
    def runSextractor(self, fname, sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']):
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(self.tmpDir, fname)
        outFile = "%s.cat"%(outpre)
        outFPath = "%s/%s"%(self.tmpDir, outFile)
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
        
    #hotpants
    def runHotpants(self, objImg, tmpImg):
        
        objpre= objImg.split(".")[0]
        tmppre= tmpImg.split(".")[0]
        objFPath = "%s/%s"%(self.tmpDir, objImg)
        tmpFPath = "%s/%s"%(self.tmpDir, tmpImg)
        outFile = "%s_%s_resi.fit"%(objpre,tmppre)
        outFPath = "%s/%s"%(self.tmpDir, outFile)
        
        # run sextractor from the unix command line
        cmd = [self.imgDiffProgram, '-inim', objFPath, '-tmplim', tmpFPath, '-outim', 
                 outFPath, '-v', '0', '-nrx', '4', '-nry', '4']
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        #self.log.info(stdoutstr)
        #self.log.info(stderrstr)
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run hotpants success.")
            self.log.debug("generate diff residual image %s"%(outFPath))
        else:
            self.log.error("hotpants failed.")
            
        return outFile
    
    
        
    def simImage(self, oImg):
    
        outpre= oImg.split(".")[0]
        os.system("rm -rf %s/*"%(self.tmpDir))
        os.system("cp %s/%s %s/%s"%(self.srcDir, oImg, self.tmpDir, self.objectImg))
        
        self.objectImgCat = self.runSextractor(self.objectImg)
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r16)
        self.osn16 = nmhFile
        
        osn16s = selectTempOTs(self.osn16, self.tmpDir)
        osn16sf = filtOTs(osn16s, self.tmpDir)
        
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
            self.simImage(timg)
            break
            
if __name__ == "__main__":
    
    otsim = GenerateCheckImage()
    otsim.batchSim()
    #otsim.testSimImage()
    #otsim.simFOT2('obj', 'tmp')
    