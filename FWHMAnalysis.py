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
import shutil
import scipy.ndimage
from PIL import Image
import subprocess
from gwac_util import zscale_image, selectTempOTs, filtOTs, filtByEllipticity, genFinalOTDs9Reg, genPSFView, getThumbnail
from imgSim import ImageSimulation

#import relevant spline libraries
from scipy.interpolate import Rbf

class FwhmTest(object):
    def __init__(self): 
        
        self.verbose = True
        
        self.varDir = "/home/xy/Downloads/myresource/deep_data2/simulate_tools"
        #self.srcDir = "/home/xy/Downloads/myresource/deep_data2/mini_gwac" # ls CombZ_*fit
        self.srcDir = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0" # ls CombZ_*fit
        #self.srcDir = "/home/xy/Downloads/myresource/deep_data2/chaodata" # ls CombZ_*fit
        self.srcDirBad = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0_bad"
        self.tmpDir="/run/shm/gwacsim"
        self.destDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data_1026"
        self.preViewDir="/home/xy/Downloads/myresource/deep_data2/simot/preview_1026"
        self.matchProgram="/home/xy/program/netbeans/C/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"
        self.imgDiffProgram="/home/xy/program/C/hotpants/hotpants"
        self.geomapProgram="/home/xy/program/netbeans/C/GWACProject/dist/Debug/GNU-Linux/gwacproject"
                
        if not os.path.exists(self.tmpDir):
            os.system("mkdir %s"%(self.tmpDir))
        if not os.path.exists(self.destDir):
            os.system("mkdir %s"%(self.destDir))
        if not os.path.exists(self.srcDirBad):
            os.system("mkdir %s"%(self.srcDirBad))
        if not os.path.exists(self.preViewDir):
            os.system("mkdir %s"%(self.preViewDir))
            
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
        
        self.imgShape = []
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
        cmd = [self.matchProgram, fullPath, str(mchRadius), '4', '5', '39'] #bg: 18, fwhm:19, mag:39
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

    def numberGridStatistic(self, imgfile, catfile, gridNum=4):
        
        catData = np.loadtxt("%s/%s"%(self.tmpDir, catfile))
        
        tpath = "%s/%s"%(self.tmpDir, imgfile)
        tdata = fits.getdata(tpath)
        imgW = tdata.shape[1]
        imgH = tdata.shape[0]
        
        tintervalW = imgW/gridNum
        tintervalH = imgH/gridNum
        
        tarray = []
        for i in range(gridNum):
            yStart = i*tintervalH
            yEnd = (i+1)*tintervalH
            #print("yStart=%d,yEnd=%d"%(yStart, yEnd))
            for j in range(gridNum):
                xStart = j*tintervalW
                xEnd = (j+1)*tintervalW
                #print("xStart=%d,xEnd=%d"%(xStart, xEnd))
                tnum = 0
                for row in catData:
                    tx = row[3]
                    ty = row[4]
                    if tx>=xStart and tx<xEnd and ty>=yStart and ty<yEnd:
                        tnum = tnum + 1
                    
                tarray.append((i,j,tnum))
        tnum2 = 0
        for trow in tarray:
            tnum2 = tnum2+ trow[2]
        print("%s total %d:%d"%(catfile, catData.shape[0], tnum2))
        print(tarray)
        return tarray
    

    def fwhmrGridStatistic(self, imgfile, catfile, gridNum=100):
        
        catData = np.loadtxt("%s/%s"%(self.tmpDir, catfile))
        
        tpath = "%s/%s"%(self.tmpDir, imgfile)
        tdata = fits.getdata(tpath)
        imgW = tdata.shape[1]
        imgH = tdata.shape[0]
        
        tintervalW = imgW/gridNum
        tintervalH = imgH/gridNum
        print("tintervalW=%d"%(tintervalW))
        print("tintervalH=%d"%(tintervalH))
                
        tbuff = []
        for i in range(gridNum):
            for j in range(gridNum):
                tbuff.append([])
        for row in catData:
            tx = row[3]
            ty = row[4]
            xIdx = math.floor(tx%tintervalW)
            yIdx = math.floor(ty%tintervalW)
            tIdx = yIdx * gridNum + xIdx
            tbuff[tIdx].append(row[19])
        
        fwhmMed = np.zeros((gridNum,gridNum), dtype=float)
        fwhmMin = np.zeros((gridNum,gridNum), dtype=float)
        fwhmMax = np.zeros((gridNum,gridNum), dtype=float)
        
        x = []
        y = []
        z = []
        for i in range(gridNum):
            for j in range(gridNum):
                tIdx = i * gridNum + j
                tfwhm = np.array(tbuff[tIdx])
                if tfwhm.shape[0]==0:
                    continue
                tmed = np.median(tfwhm)
                tmin = np.min(tfwhm)
                tmax = np.max(tfwhm)
                fwhmMed[i][j] = tmed
                fwhmMin[i][j] = tmin
                fwhmMax[i][j] = tmax
                x.append(j)
                y.append(i)
                z.append(tmed)
        
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.plot_trisurf(x, y, z, linewidth=0.2, antialiased=True)
        plt.show()

    def fwhm(self, oImg):
        
        self.objectImgOrig = oImg
        os.system("rm -rf %s/*"%(self.tmpDir))
        os.system("cp %s %s/%s"%(oImg, self.tmpDir, self.objectImg))
        self.removeHeader(self.objectImg)
        
        self.objectImgCat = self.runSextractor(self.objectImg)
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, self.objectImgCat))
        print("objImg extract star %d"%(tdata.shape[0]))
        if len(tdata.shape)<2 or tdata.shape[0]<5000:
            print("%s has too little stars, break this run"%(oImg))
            return
        
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r16)
        self.osn16 = nmhFile
        
        tarray = self.numberGridStatistic(self.objectImg, self.osn16, gridNum=4)
        print(tarray)
    
    def test2(self):
        
        objectImg = 'oi.fit'
        osn16 = "oi_sn16.cat"
        tarray = self.numberGridStatistic(objectImg, osn16, gridNum=4)
        print(tarray)
        self.fwhmrGridStatistic(objectImg, osn16, gridNum=100)
        
        
    def test(self):
        
        timg1 = "/home/xy/Downloads/myresource/deep_data2/mini_gwac/M2_03_171118_1_010020_1000.fits"
        timg2 = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0/G044_mon_objt_180416T14044944.fit" #jfov
        timg3 = "/home/xy/Downloads/myresource/deep_data2/chaodata/CombZ_101.fit"
        timg4 = "/home/xy/Downloads/myresource/deep_data2/G181108/G035_mon_objt_181108T15443856.fit.fz" #ffov
        
        self.fwhm(timg2)
            
if __name__ == "__main__":
    
    otsim = FittingTest()
    otsim.batchSim()
    #otsim.test()
    #otsim.simFOT2('obj', 'tmp')
    