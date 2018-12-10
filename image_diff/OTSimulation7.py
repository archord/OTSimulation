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
from gwac_util import getThumbnail, getThumbnail_, zscale_image

class OTSimulation(object):
    def __init__(self): 
        
        self.verbose = True
        
        self.varDir = "/home/xy/Downloads/myresource/deep_data2/simulate_tools"
        #self.srcDir = "/home/xy/Downloads/myresource/deep_data2/mini_gwac" # ls CombZ_*fit
        self.srcDir = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0"
        #self.srcDir = "/home/xy"
        #self.srcDir = "/home/xy/Downloads/myresource/deep_data2/chaodata" # ls CombZ_*fit
        self.srcDirBad = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0_bad"
        self.tmpDir="/run/shm/gwacsim"
        self.destDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data_1026"
        self.preViewDir="/home/xy/Downloads/myresource/deep_data2/simot/preview_1026"
        self.matchProgram="/home/xy/program/netbeans/C/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"
        self.imgDiffProgram="/home/xy/Downloads/myresource/deep_data2/hotpants/hotpants"
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
        cmd = [self.matchProgram, fullPath, str(mchRadius), '2', '3', '13']
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
        cmd = [self.matchProgram, tmpFPath, objFPath, outFPath, str(mchRadius), '2', '3', '13']
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
    def runSextractor(self, fname, fpar='OTsearch.par', sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3'], fconf='OTsearch.sex'):
        
        starttime = datetime.datetime.now()
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(self.tmpDir, fname)
        outFile = "%s.cat"%(outpre)
        outFPath = "%s/%s"%(self.tmpDir, outFile)
        cnfPath = "%s/config/%s"%(self.varDir, fconf)
        outParmPath = "%s/config/%s"%(self.varDir, fpar) #sex_diff.par  OTsearch.par  sex_diff_fot.par
        outCheckPath = "%s/%s_bkg.fit"%(self.tmpDir, outpre)
        
        #DETECT_MINAREA   5              # minimum number of pixels above threshold
        #DETECT_THRESH    3.0             #  <sigmas>  or  <threshold>,<ZP>  in  mag.arcsec-2  
        #ANALYSIS_THRESH  3.0
        # run sextractor from the unix command line
        cmd = ['sex', fullPath, '-c', cnfPath, '-CATALOG_NAME', outFPath, '-PARAMETERS_NAME', outParmPath,
               '-CHECKIMAGE_TYPE', 'BACKGROUND', '-CHECKIMAGE_NAME', outCheckPath]
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
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("run sextractor use %d seconds"%(runTime))
            
        return outFile
    
        #hotpants
    def runHotpants(self, objImg, tmpImg):
        
        starttime = datetime.datetime.now()
        
        objpre= objImg.split(".")[0]
        tmppre= tmpImg.split(".")[0]
        objFPath = "%s/%s"%(self.tmpDir, objImg)
        tmpFPath = "%s/%s"%(self.tmpDir, tmpImg)
        outFile = "%s_%s_resi.fit"%(objpre,tmppre)
        outFPath = "%s/%s"%(self.tmpDir, outFile)
        
        # run sextractor from the unix command line
        #/home/xy/program/C/hotpants/hotpants -inim oi.fit -tmplim ti.fit -outim oi_ti_resi.fit -v 0 -nrx 4 -nry 4
        cmd = [self.imgDiffProgram, '-inim', objFPath, '-tmplim', tmpFPath, '-outim', 
                 outFPath, '-v', '0', '-nrx', '4', '-nry', '4', '-nsx', '6', '-nsy', '6', '-r', '6']
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
            
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("run hotpants use %d seconds"%(runTime))
            
        return outFile
                
    def removeHeaderAndOverScan(self, fname):
        
        imgSize = (4136, 4196)
        overscanLeft = 20
        overscanRight = 80
        fullPath = "%s/%s"%(self.tmpDir, fname)
        
        fname='G022_mon_objt_180226T17492514_2.fits'
        keyword=['WCSASTRM','WCSDIM','CTYPE1','CTYPE2',
                 'CRVAL1','CRVAL2','CRPIX1','CRPIX2',
                 'CD1_1','CD1_2','CD2_1','CD2_2','WAT0_001',
                 'WAT1_001','WAT1_002','WAT1_003','WAT1_004','WAT1_005','WAT1_006','WAT1_007','WAT1_008',
                 'WAT2_001','WAT2_002','WAT2_003','WAT2_004','WAT2_005','WAT2_006','WAT2_007','WAT2_008']
    
        with fits.open(fullPath, mode='update') as hdul:
            hdu1 = hdul[0]
            hdr = hdu1.header
            for kw in keyword:
                hdr.remove(kw,ignore_missing=True)
            data = hdu1.data
            hdu1.data = data[:,overscanLeft:-overscanRight]
            hdul.flush()
            hdul.close()

    def gridStatistic(self, catfile, gridNum=4):
        
        catData = np.loadtxt("%s/%s"%(self.tmpDir, catfile))
        
        '''
        tpath = "%s/%s"%(self.tmpDir, self.objectImg)
        tdata = fits.getdata(tpath)
        imgW = tdata.shape[1]
        imgH = tdata.shape[0]
        '''
        
        #imgSize = (4136, 4196)
        imgSize = (4136, 4096)
        imgW = imgSize[1]
        imgH = imgSize[0]
        
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
    
    def getMatchPos(self, oiFile, tiFile, mchPair, rmsTimes=2):

        starttime = datetime.datetime.now()
        
        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, oiFile))
        tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, tiFile))
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair)).astype(np.int)
        
        print("osn16:%d tsn16:%d osn16_tsn16_cm5:%d"%(tdata1.shape[0], tdata2.shape[0],tIdx1.shape[0]))
        
        tIdx1 = tIdx1 - 1
        pos1 = tdata1[tIdx1[:,0]][:,0:2]
        pos2 = tdata2[tIdx1[:,1]][:,0:2]
        
        dataOi = pos1
        dataTi = pos2
        
        tpath = "%s/%s"%(self.tmpDir, self.objectImg)
        tData = fits.getdata(tpath)
        
        h, status = cv2.findHomography(dataOi, dataTi, cv2.RANSAC, 0.1) #0, RANSAC , LMEDS
        newimage = cv2.warpPerspective(tData, h, (tData.shape[1],tData.shape[0]))
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("opencv remap sci image use %.2f seconds"%(runTime))
        
        return newimage, h

    def processBadPix(self):
        
        starttime = datetime.datetime.now()
        
        objName = 'ti.fit'
        bkgName = 'ti_bkg.fit'
        
        objPath = "%s/%s"%(self.tmpDir, objName)
        bkgPath = "%s/%s"%(self.tmpDir, bkgName)
        
        objData = fits.getdata(objPath)
        bkgData = fits.getdata(bkgPath)
        
        tIdx = objData<bkgData
        bkgData[tIdx] = objData[tIdx]
        bkgMax = np.max(bkgData)
        
        bkgData = 1 + bkgMax -bkgData
        '''
        newName = "badpix1.fit"
        newPath = "%s/%s"%(self.tmpDir, newName)
        if os.path.exists(newPath):
            os.remove(newPath)
        hdu = fits.PrimaryHDU(bkgData)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath)
        '''
        
        starttime1 = datetime.datetime.now()
        bkgData = bkgData.astype(np.uint16)
        #bkgData = mean(bkgData, square(3))
        #kernel = np.ones((3,3),np.float32)/25
        #dst = cv2.filter2D(bkgData,-1,kernel)
        bkgData = cv2.blur(bkgData,(3,3)) #faster than mean
        bkgData = bkgData.astype(np.uint16)
        
        endtime1 = datetime.datetime.now()
        runTime1 = (endtime1 - starttime1).seconds
        self.log.debug("process badpix meanfilter use %d seconds"%(runTime1))
        
        newName = "badpix.fit"
        newPath = "%s/%s"%(self.tmpDir, newName)
        if os.path.exists(newPath):
            os.remove(newPath)
        hdu = fits.PrimaryHDU(bkgData)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath)

        fpar='sex_diff.par'
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        resultCat = self.runSextractor(newName, fpar, sexConf)
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, resultCat))
        
        fluxMax = tdata[:,5]
        fluxMaxMean = np.mean(fluxMax)
        fluxMaxStd = np.std(fluxMax)
        fluxMaxThd = fluxMaxMean+2*fluxMaxStd #(μ—2σ,μ+2σ) 0.9544
        tidx = fluxMax>fluxMaxThd 
        print("badpix star %d, fluxMaxMean=%.2f, fluxMaxStd=%.2f, fluxMaxThd=%.2f"%(tdata.shape[0], fluxMaxMean, fluxMaxStd, fluxMaxThd))
        
        tdata = tdata[tidx]
        
        print("badpix flux_max>background star %d"%(tdata.shape[0]))
        ds9RegionName = "%s/%s_ds9.reg"%(self.tmpDir, resultCat[:resultCat.index(".")])
        with open(ds9RegionName, 'w') as fp1:
            for tobj in tdata:
               fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%ld-%.2f} font=\"times 10\"\n"%
               (tobj[1], tobj[2], 4.0, tobj[5], tobj[9]))
        
        selposName = "%s_sel.cat"%(resultCat[:resultCat.index(".")])
        selposPath = "%s/%s"%(self.tmpDir, selposName)
        with open(selposPath, 'w') as fp1:
            for tobj in tdata:
               fp1.write("%.3f %.3f %.3f\n"%(tobj[1], tobj[2], tobj[12]))
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("process badpix use %d seconds"%(runTime))
        
        return selposName
        
    def simImage(self, oImg, tImg):
        
        starttime = datetime.datetime.now()
        
        self.objectImgOrig = oImg
        self.templateImgOrig = tImg
    
        os.system("rm -rf %s/*"%(self.tmpDir))
                
        os.system("cp %s/%s %s/%s"%(self.srcDir, oImg, self.tmpDir, self.objectImg))
        os.system("cp %s/%s %s/%s"%(self.srcDir, tImg, self.tmpDir, self.templateImg))
        
        self.removeHeaderAndOverScan(self.objectImg)
        self.removeHeaderAndOverScan(self.templateImg)

        sexConf=['-DETECT_MINAREA','7','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff_fot.par'
        self.objectImgCat = self.runSextractor(self.objectImg, fpar, sexConf)
        self.templateImgCat = self.runSextractor(self.templateImg, fpar, sexConf)
        
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
        
        badPixCat = self.processBadPix()
        
        '''  '''
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r16)
        self.osn16 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.templateImgCat, self.r16)
        self.tsn16 = nmhFile
        
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.osn16, self.tsn16, 10)
        osn16_tsn16_cm5 = mchFile
        osn16_tsn16_cm5_pair = mchPair
        
        self.gridStatistic(osn16_tsn16_cm5, gridNum=4)
        
        newimage, h = self.getMatchPos(self.osn16, self.tsn16, osn16_tsn16_cm5_pair)
                
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
        resImg = self.runHotpants(newName, self.templateImg)
        timg = getThumbnail(self.tmpDir, resImg, stampSize=(100,100), grid=(5, 5), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, 4, order=0)

        plt.figure(figsize = (12, 12))
        plt.imshow(timg, cmap='gray')
        plt.show()
        
        fpar='sex_diff.par'
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        resiCat = self.runSextractor(resImg, fpar, sexConf)
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, resiCat))
        print("resi image star %d"%(tdata.shape[0]))
        
        mchRadius = 5
        mchFile, nmhFile, mchPair = self.runCrossMatch(resiCat, self.templateImgCat, mchRadius)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
        print("resi star match template %d"%(tdata.shape[0]))
        
        mchFile, nmhFile, mchPair = self.runCrossMatch(mchFile, badPixCat, mchRadius)
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, nmhFile))
        print("resi star match template and remove badpix %d"%(tdata.shape[0]))
        

        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("image diff total use %d seconds"%(runTime))
        
        
    def test2(self):
        
        osn16 = "oi_sn16.cat"
        tsn16 = "ti_sn16.cat"
        osn16_tsn16_cm5_pair= "oi_sn16_ti_sn16_cm10.pair"
        #self.getMatchPos(osn16, tsn16, osn16_tsn16_cm5_pair, rmsTimes=0.5)
        self.getMatchPos(osn16, tsn16, osn16_tsn16_cm5_pair, rmsTimes=1)
        
    def test(self):
        
        #objectImg = 'CombZ_0.fit'
        #templateImg = 'CombZ_101.fit'
        objectImg = 'G044_mon_objt_181121T18300131.fit'
        templateImg = 'G044_mon_objt_181121T16100132.fit'
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
    
    otsim = OTSimulation()
    otsim.batchSim()
    #otsim.test()
    #otsim.simFOT2('obj', 'tmp')
    