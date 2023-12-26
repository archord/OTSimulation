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


class FittingTest(object):
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

    def runGeoXYTran(self, posIn, mapParm, direction='-1'):
        
        preStr= posIn[:-4]
        outFileName = "%s_tran.cat"%(preStr)
        tpathIn = "%s/%s"%(self.tmpDir, posIn)
        tpathOut = "%s/%s"%(self.tmpDir, outFileName)
        tpath2 = "%s/%s"%(self.tmpDir, mapParm)
        
        #exeprog geoxytran data.cat mapParm.txt data.out direction=-1
        cmd = [self.geomapProgram, "geoxytran", tpathIn, tpath2, tpathOut, direction]
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        if os.path.exists(tpath2) and status==0:
            self.log.debug("run geoxytran success.")
            self.log.debug("generate geoxytran parameter file %s"%(tpath2))
        else:
            self.log.error("geoxytran failed.")
        
        return outFileName

    def runGeoMap(self, coorCat, order=5, iterNum=4, rejSigma=2.5):
        
        preStr= coorCat[:-4]
        geoMapParm = "%s_geomap.txt"%(preStr)
        tpath1 = "%s/%s"%(self.tmpDir, coorCat)
        tpath2 = "%s/%s"%(self.tmpDir, geoMapParm)
        
        #exeprog geomap pairs.cat map_parm.txt order=5 iterNum=4 rejSigma=2.5
        cmd = [self.geomapProgram, "geomap", tpath1, tpath2, '5', '4', '2.5']
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        if os.path.exists(tpath2) and status==0:
            self.log.debug("run geomap success.")
            self.log.debug("generate geomap parameter file %s"%(tpath2))
        else:
            self.log.error("geomap failed.")
        
        return geoMapParm
    
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

    def gridStatistic(self, catfile, gridNum=4):
        
        catData = np.loadtxt("%s/%s"%(self.tmpDir, catfile))
        
        tpath = "%s/%s"%(self.tmpDir, self.objectImg)
        tdata = fits.getdata(tpath)
        imgW = tdata.shape[1]
        imgH = tdata.shape[0]
        
        tintervalW = imgW/gridNum
        tintervalH = imgH/gridNum
        
        tarray = []
        for i in range(gridNum):
            yStart = i*tintervalH
            yEnd = (i+1)*tintervalH
            for j in range(gridNum):
                xStart = j*tintervalW
                xEnd = (j+1)*tintervalW
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
        
    def gridStatistic2(self, imgfile, catfile, gridNum=4):
        
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
            for j in range(gridNum):
                xStart = j*tintervalW
                xEnd = (j+1)*tintervalW
                tnum = 0
                for row in catData:
                    tx = row[0]
                    ty = row[1]
                    if tx>=xStart and tx<xEnd and ty>=yStart and ty<yEnd:
                        tnum = tnum + 1
                    
                tarray.append((i,j,tnum))
        tnum2 = 0
        for trow in tarray:
            tnum2 = tnum2+ trow[2]
        print("%s total %d:%d"%(catfile, catData.shape[0], tnum2))
        print(tarray)
                

    def simImage(self, oImg, tImg):
        
        self.objectImgOrig = oImg
        self.templateImgOrig = tImg
    
        os.system("rm -rf %s/*"%(self.tmpDir))
                
        os.system("cp %s/%s %s/%s"%(self.srcDir, oImg, self.tmpDir, self.objectImg))
        os.system("cp %s/%s %s/%s"%(self.srcDir, tImg, self.tmpDir, self.templateImg))
        
        self.removeHeader(self.objectImg)
        self.removeHeader(self.templateImg)
        
        self.objectImgCat = self.runSextractor(self.objectImg)
        self.templateImgCat = self.runSextractor(self.templateImg)
        
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
        
        #查找“真OT”，如小行星等
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.objectImgCat, self.templateImgCat, self.r5)
        self.obj_tmp_cm5 = mchFile
        self.obj_tmp_cn5 = nmhFile
        
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r16)
        self.osn16 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.templateImgCat, self.r16)
        self.tsn16 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r5)
        self.osn5 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.templateImgCat, self.r5)
        self.tsn5 = nmhFile
        
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.osn16, self.tsn16, 10)
        osn16_tsn16_cm5 = mchFile
        osn16_tsn16_cm5_pair = mchPair
        
        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, self.osn16))
        tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, self.tsn16))
        tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, osn16_tsn16_cm5))
        
        print("osn16:%d tsn16:%d osn16_tsn16_cm5:%d"%(tdata1.shape[0], tdata2.shape[0],tdata3.shape[0]))
        self.gridStatistic(osn16_tsn16_cm5, gridNum=4)
        
        
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, osn16_tsn16_cm5_pair)).astype(np.int)
        tIdx1 = tIdx1 - 1
        pos1 = tdata1[tIdx1[:,0]][:,3:5]
        pos2 = tdata2[tIdx1[:,1]][:,3:5]
        posDiff = pos1-pos2
        
        posMean = np.mean(posDiff, axis=1)
        posMin = np.min(posDiff, axis=1)
        posMax = np.max(posDiff, axis=1)
        
        print(posMean)
        print(posMin)
        print(posMax)
        
    def saveResidual2Regions(self, fname, pos, diff, rmsTimes):
        
        tNameReg = "%s_posdiff%.1f.reg"%(fname.split('.')[0], rmsTimes)
        ds9RegionName1 = "%s/%s"%(self.tmpDir, tNameReg)
        with open(ds9RegionName1, 'w') as fp1:
            for ii, tobj in enumerate(pos):
               fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f,%.2f} font=\"times 10\"\n"%
               (tobj[0], tobj[1], 2.0, diff[ii][0], diff[ii][1]))
    
    def getMatchPos(self, oiFile, tiFile, mchPair, rmsTimes=2):

        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, oiFile))
        tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, tiFile))
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair)).astype(np.int)
        
        tIdx1 = tIdx1 - 1
        pos1 = tdata1[tIdx1[:,0]][:,3:5]
        pos2 = tdata2[tIdx1[:,1]][:,3:5]
        posDiff = pos1-pos2
                
        posMean = np.mean(posDiff, axis=0)
        posMin = np.min(posDiff, axis=0)
        posMax = np.max(posDiff, axis=0)
        posRms = np.std(posDiff, axis=0)
                
        posDiffAbs = np.abs(posDiff)
        posMeanAbs = np.abs(posMean)

        xIdx = posDiffAbs[:,0]<posMeanAbs[0]+rmsTimes*posRms[0]
        yIdx = posDiffAbs[:,1]<posMeanAbs[1]+rmsTimes*posRms[0]
        
        dataOi = pos1[xIdx & yIdx]
        dataTi = pos2[xIdx & yIdx]
        print("%d, %.1f rms filter remove %d, left %d"%(pos1.shape[0],rmsTimes, pos1.shape[0]-dataOi.shape[0], dataOi.shape[0]))

        '''  
        posDiffAll = posDiff[xIdx & yIdx]
        self.saveResidual2Regions(oiFile, dataOi, posDiffAll, rmsTimes)
        self.saveResidual2Regions(tiFile, dataTi, posDiffAll, rmsTimes)
        self.gridStatistic2("oi.fit", tName, gridNum=4)
        '''
        
        tName = "%s_%s_mchpairs%.1f.cat"%(oiFile.split('.')[0], tiFile.split('.')[0], rmsTimes)
        mchpairPath = "%s/%s"%(self.tmpDir, tName)
        with open(mchpairPath, 'w') as fp1:
            for ii, tobj in enumerate(dataOi):
               fp1.write("%.3f %.3f %.3f %.3f\n"%
               (dataOi[ii][0],dataOi[ii][1],dataTi[ii][0],dataTi[ii][1]))
        
        geoMapParm = self.runGeoMap(tName)
        
        tpath = "%s/%s"%(self.tmpDir, self.objectImg)
        tdata = fits.getdata(tpath)
        imgW = tdata.shape[1]
        imgH = tdata.shape[0]
        
        tInterval = 1
        xIdx = np.arange(0,imgW+1,tInterval)
        yIdx = np.arange(0,imgH+1,tInterval)
        poss = []
        for ty in yIdx:
            for tx in xIdx:
                poss.append((tx,ty))
        
        tName = "sim_poss.cat"
        mchpairPath = "%s/%s"%(self.tmpDir, tName)
        with open(mchpairPath, 'w') as fp1:
            for tobj in poss:
               fp1.write("%.3f %.3f %.3f %.3f\n"%
               (tobj[0], tobj[1], tobj[0], tobj[1])) 
        
        posTran = self.runGeoXYTran(tName, geoMapParm, direction='-1')
        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, posTran))
        posX = []
        posY = []
        for tdata in tdata1:
            posX.append(tdata[0])
            posY.append(tdata[1])
            
        grid = np.array([posY.reshape(tdata.shape), posX.reshape(tdata.shape)])
        print(grid.shape)
        print(grid)
        
    def test2(self):
        
        osn16 = "oi_sn16.cat"
        tsn16 = "ti_sn16.cat"
        osn16_tsn16_cm5_pair= "oi_sn16_ti_sn16_cm10.pair"
        #self.getMatchPos(osn16, tsn16, osn16_tsn16_cm5_pair, rmsTimes=0.5)
        self.getMatchPos(osn16, tsn16, osn16_tsn16_cm5_pair, rmsTimes=1)

    def test3(self):
        
        tpath = "%s/%s"%(self.tmpDir, self.objectImg)
        tdata = fits.getdata(tpath)
        imgW = tdata.shape[1]
        imgH = tdata.shape[0]
        
        tInterval = 10
        xIdx = np.arange(0,imgW+1,tInterval)
        yIdx = np.arange(0,imgH+1,tInterval)
        poss = []
        for ty in yIdx:
            for tx in xIdx:
                poss.append((tx,ty))
        
        tName = "sim_poss.cat"
        mchpairPath = "%s/%s"%(self.tmpDir, tName)
        with open(mchpairPath, 'w') as fp1:
            for tobj in poss:
               fp1.write("%.3f %.3f %.3f %.3f\n"%
               (tobj[0], tobj[1], tobj[0], tobj[1])) 
        
        geoMapParm = "oi_sn16_ti_sn16_mchpairs1.0_geomap.txt"
        posTran = self.runGeoXYTran(tName, geoMapParm, direction='-1')
        
        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, posTran))
        posX = []
        posY = []
        for tdata in tdata1:
            posX.append(tdata[0])
            posY.append(tdata[1])
        
        grid = np.array([posY.reshape(tdata.shape), posX.reshape(tdata.shape)])
        print(grid.shape)
        print(grid)
        
        '''
        plt.figure(figsize = (70, 70))
        plt.plot(posX, posY, '.')
        #plt.savefig('%s/aaa.png'%(self.tmpDir),dpi=900)
        plt.savefig('aaa.png')
        #plt.show()
        '''
        
    def test(self):
        
        #objectImg = 'CombZ_0.fit'
        #templateImg = 'CombZ_101.fit'
        objectImg = 'M2_03_171118_1_010020_1100.fits'
        templateImg = 'M2_03_171118_1_010020_0900.fits'
        self.simImage(objectImg, templateImg)
        
        
    def batchSim(self):
        
        flist = os.listdir(self.srcDir)
        flist.sort()
        
        imgs = []
        for tfilename in flist:
            if tfilename.find("fit")>-1:
                imgs.append(tfilename)
        
        print("total image %d"%(len(imgs)))
        objectImg = imgs[500]
        templateImg = imgs[50]
        self.simImage(objectImg, templateImg)
            
if __name__ == "__main__":
    
    otsim = FittingTest()
    otsim.batchSim()
    #otsim.test()
    #otsim.simFOT2('obj', 'tmp')
    