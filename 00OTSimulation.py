# -*- coding: utf-8 -*-

import scipy as S
import numpy as np
import matplotlib.pyplot as plt
from astropy.stats import sigma_clip
from astropy.io import fits
from random import randint
import sys
import os
import logging
import subprocess


class OTSimulation(object):
    def __init__(self):
        
        self.varDir = "/home/xy/Downloads/myresource/deep_data2/simulate_tools"
        self.srcDir = "/home/xy/Downloads/myresource/deep_data2/chaodata" # ls CombZ_*fit
        self.tmpDir="/run/shm/gwacsim"
        self.destDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data"
        self.matchProgram="/home/xy/program/netbeans/C/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"
        self.imgDiffProgram="/home/xy/program/C/hotpants/hotpants"
        
        self.log = logging.getLogger() #create logger
        self.log.setLevel(logging.DEBUG) #set level of logger
        
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
        
        self.r5 = 5
        self.r10 = 10
        self.r16 = 16
        self.r32 = 32
    
    def selectTempOTs(self, fname, printFlag=False):
    #   1 NUMBER                 Running object number                                     
    #   2 ALPHA_J2000            Right ascension of barycenter (J2000)                      [deg]
    #   3 DELTA_J2000            Declination of barycenter (J2000)                          [deg]
    #   4 X_IMAGE                Object position along x                                    [pixel]
    #   5 Y_IMAGE                Object position along y                                    [pixel]
    #  13 A_IMAGE                Profile RMS along major axis                               [pixel]
    #  14 B_IMAGE                Profile RMS along minor axis                               [pixel]
    #  15 ELONGATION             A_IMAGE/B_IMAGE                                           
    #  16 ELLIPTICITY            1 - B_IMAGE/A_IMAGE                                       
    #  17 CLASS_STAR             S/G classifier output                                     
    #  18 BACKGROUND             Background at centroid position                            [count]
    #  19 FWHM_IMAGE             FWHM assuming a gaussian core                              [pixel]
    #  20 FLUX_RADIUS            Fraction-of-light radii                                    [pixel]
    #  30 FLAGS                  Extraction flags                                          
    #  39 MAG_APER               Fixed aperture magnitude vector                            [mag]
    #  40 MAGERR_APER            RMS error vector for fixed aperture mag.                   [mag]
        tdata = np.loadtxt(fname)
        origSize = tdata.shape
    
        maxEllipticity = 0.1
        mag = tdata[:,38]
        elpct = tdata[:,15]
        fwhm = tdata[:,18]
        
        mag1 = sigma_clip(mag, sigma=2.5, iters=3)
        minMag = np.min(mag1)
        maxMag = np.max(mag1)
        medianFwhm = np.median(fwhm)
        
        targetFwhmMax = medianFwhm
        targetMag = maxMag-6
        targetMagMin = targetMag+1
        targetMagMax = targetMag+3
        tdata = tdata[(mag>targetMagMin) & (mag<targetMagMax) & (elpct<maxEllipticity) & (fwhm<targetFwhmMax)]
        
        if printFlag:
            print("total read %d objects"%(origSize[0]))
            print("mag range from %f to %f, select mag from %f to %f"%(minMag, maxMag, targetMagMin, targetMagMax))
            print("with ellipticity less than %f, and fwhm less than %f"%(maxEllipticity, targetFwhmMax))
            print("after filter, left %d objects"%(tdata.shape[0]))
            
            ds9RegionName = fname[:fname.index(".")] + "_ottempsel_ds9.reg"
            with open(ds9RegionName, 'w') as fp1:
                for tobj in tdata:
                   fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%ld-%.2f} font=\"times 7\"\n"%
                   (tobj[3], tobj[4], 4.0, tobj[0], tobj[38]))
                   
               
        ots = []
        for tobj in tdata:
            ots.append((tobj[3],tobj[4],tobj[38]))
        maxInstrMag = maxMag
        
        self.log.debug("selectTempOTs done.")
        
        return ots, maxInstrMag
    
    '''
    选择部分假OT，过滤条件：
    1）过滤最暗的magRatio（5%）
    2）过滤图像边缘的fSize（200px）
    '''
    def filtOTs(self, fname, magRatio=0.05, fSize=200, imgSize=[4096,4096], printFlag=False):
    
        tdata = np.loadtxt(fname)
        
        minX = 0 + fSize
        minY = 0 + fSize
        maxX = imgSize[0] - fSize
        maxY = imgSize[1] - fSize
    
        mag = tdata[:,38]
        mag = np.sort(mag)
        maxMag = mag[int((1-magRatio)*tdata.shape[0])]
        
        tobjs = []
        for obj in tdata:
            tx = obj[3]
            ty = obj[4]
            tmag = tdata[38]
            if tx>minX and tx <maxX and ty>minY and ty<maxY and tmag<maxMag:
                tobjs.append([tx, ty, tmag])
                
        outCatName = "%sf.cat"%(fname[:fname.index(".")])
        with open(outCatName, 'w') as fp0:
            for tobj in tobjs:
               fp0.write("%.2f,%.2f,%.2f\n"%(tobj[0], tobj[1], tobj[2]))
                   
        if printFlag:
            print("total read %d objects"%(tdata.shape[0]))
            print("filter maxMag %f"%(maxMag))
            print("after filter, left %d objects"%(len(tobjs)))
            
            ds9RegionName = "%s_filter_ds9.reg"%(fname[:fname.index(".")])
            with open(ds9RegionName, 'w') as fp1:
                for tobj in tobjs:
                   fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 12\"\n"%
                   (tobj[0], tobj[1], 4.0, tobj[2]))
               
        return outCatName    
    
    #catalog self match
    def runSelfMatch(self, fname, mchRadius):
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(self.tmpDir, fname)
        
        # run sextractor from the unix command line
        cmd = [self.matchProgram, fullPath, mchRadius, '4', '5', '39']
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        mchFile = "%s/%s_sm%d.cat"%(self.tmpDir, outpre,mchRadius)
        nmhFile = "%s/%s_sn%d.cat"%(self.tmpDir, outpre,mchRadius)
        if os.path.exists(mchFile) and os.path.exists(nmhFile) and status==0:
            self.log.debug("run catalog match success.")
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
        cmd = [self.matchProgram, tmpFPath, objFPath, outFPath, mchRadius, '4', '5', '39']
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        mchPair = "%s/%s_%s_cm%d.pair"%(self.tmpDir, objpre,tmppre,mchRadius)
        mchFile = "%s/%s_%s_cm%d.cat"%(self.tmpDir, objpre,tmppre,mchRadius)
        nmhFile = "%s/%s_%s_cn%d.cat"%(self.tmpDir, objpre,tmppre,mchRadius)
        if os.path.exists(mchFile) and os.path.exists(nmhFile) and status==0:
            self.log.debug("run catalog match success.")
            self.log.debug("generate pair file %s"%(mchPair))
            self.log.debug("generate matched file %s"%(mchFile))
            self.log.debug("generate not matched file %s"%(nmhFile))
        else:
            self.log.error("cross match failed.")
        
        return mchFile, nmhFile, mchPair
    
    #source extract
    def runSextractor(self, fname):
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(self.tmpDir, fname)
        outFPath = "%s/%s.cat"%(self.tmpDir, outpre)
        cnfPath = "%s/config/OTsearch.sex"%(self.varDir)
        
        # run sextractor from the unix command line
        cmd = ['sex', fullPath, '-c', cnfPath, '-CATALOG_NAME', outFPath]
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run catalog match success.")
            self.log.debug("generate catalog %s"%(outFPath))
        else:
            self.log.error("sextractor failed.")
            
        return outFPath
        
    #hotpants
    def runHotpants(self, objImg, tmpImg):
        
        objpre= objImg.split(".")[0]
        tmppre= tmpImg.split(".")[0]
        objFPath = "%s/%s"%(self.tmpDir, objImg)
        tmpFPath = "%s/%s"%(self.tmpDir, tmpImg)
        outFPath = "%s/%s_%s_resi.fit"%(self.tmpDir, objpre,tmppre)
        
        # run sextractor from the unix command line
        cmd = [self.imgDiffProgram, '-inim', objFPath, '-tmplim', tmpFPath, '-outim', 
                 outFPath, '-v', '0', '-nrx', '4', '-nry', '4']
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run catalog match success.")
            self.log.debug("generate diff residual image %s"%(outFPath))
        else:
            self.log.error("diff image failed.")
            
        return outFPath
    
    def simFOT(self, oImg, tImg):
        
        self.objTmpResi = self.runHotpants(self.objectImg, self.templateImg)
        self.objTmpResiCat = self.runSextractor(self.objTmpResi)
        
        #过滤“真OT”，如小行星等
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.objTmpResiCat, self.obj_tmp_cn5, self.r5)
        otr_otcn5_cn5 = nmhFile
        otr_otcn5_cn5f = self.filtOTs(otr_otcn5_cn5,printFlag=True)
        
        mchFile1, nmhFile1, mchPair1 = self.runCrossMatch(otr_otcn5_cn5f, self.osn5, self.r5)
        mchFile2, nmhFile2, mchPair2 = self.runCrossMatch(otr_otcn5_cn5f, self.tsn5, self.r5)
        
        tIdx1 = np.loadtxt(mchPair1)
        tIdx2 = np.loadtxt(mchPair2)
        self.log.debug("objectCat matched data %d, templateCat matched data %d"%(len(tdata1), len(tdata2)))
        
        tdata1 = np.loadtxt(otr_otcn5_cn5f)
        tdata2 = np.loadtxt(self.osn5)
        tdata3 = np.loadtxt(self.tsn5)
        
        tdata11 = tdata1[tIdx1[:0]]
        tdata12 = tdata2[tIdx1[:1]]
        self.log.debug("objectCat matched data %d, %d"%(len(tdata11), len(tdata12)))
        tdata21 = tdata1[tIdx2[:0]]
        tdata22 = tdata3[tIdx2[:1]]
        self.log.debug("templateCat matched data %d, %d"%(len(tdata21), len(tdata22)))
        
        
        
        
    def simTOT(self, oImg, tImg):
        
        origSamp16OTs, maxInstrMag = self.selectTempOTs(self.osn16, printFlag=True)
        
    def simImage(self, oImg, tImg):
    
        os.system("rm -rf %s/*"%(self.tmpDir))
                
        os.system("cp %s/%s %s/%s"%(self.srcDir, oImg, self.tmpDir, self.objectImg))
        os.system("cp %s/%s %s/%s"%(self.srcDir, tImg, self.tmpDir, self.templateImg))
        
        self.objectImgCat = self.runSextractor(self.objectImg)
        self.templateImgCat = self.runSextractor(self.templateImg)
        #查找“真OT”，如小行星等
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.objectImgCat, self.templateImgCat, self.r5)
        self.obj_tmp_cm5 = mchFile
        self.obj_tmp_cn5 = nmhFile
        
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r16)
        self.osn16 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r5)
        self.osn5 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.templateImgCat, self.r5)
        self.tsn5 = nmhFile
        
        
        self.simFOT(self.objectImg, self.templateImg)
        
        
    def testSimImage(self):
        
        if not os.path.exists(self.tmpDir):
            os.system("mkdir %s"%(self.tmpDir))
        
        objectImg = 'CombZ_0.fit'
        templateImg = 'CombZ_temp.fit'
        self.simFOT(objectImg, templateImg)
    
    def batchSim(self):
    
        if not os.path.exists(self.tmpDir):
            os.system("mkdir %s"%(self.tmpDir))
            
        flist = os.listdir(self.srcDir)
        flist.sort()
        for tfilename in flist:
            if tfilename.find("jpg")>-1:
                tpath = "%s/%s"%(self.srcDir, tfilename)
            
if __name__ == "__main__":
    
    otsim = OTSimulation()
    otsim.testSimImage()
    