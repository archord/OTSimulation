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

#同时输出真OT和假OT样本
class OTSimulation(object):
    def __init__(self):
        
        self.verbose = True
        
        self.varDir = "/home/xy/Downloads/myresource/deep_data2/simulate_tools"
        self.srcDir = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0" # ls CombZ_*fit
        self.srcDirBad = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0_bad"
        self.tmpDir="/run/shm/gwacsim"
        self.destDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data_1026"
        self.preViewDir="/home/xy/Downloads/myresource/deep_data2/simot/preview_1026"
        self.matchProgram="/home/xy/program/netbeans/C/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"
        self.imgDiffProgram="/home/xy/program/C/hotpants/hotpants"
                
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
    
    def getWindowImg(self, img, ctrPos, size):
        
        imgSize = img.shape
        hsize = int(size/2)
        tpad = int(size%2)
        ctrX = math.ceil(ctrPos[0])
        ctrY = math.ceil(ctrPos[1])
        
        minx = ctrX - hsize
        maxx = ctrX + hsize + tpad
        miny = ctrY - hsize
        maxy = ctrY + hsize + tpad
        
        widImg = []
        if minx>0 and miny>0 and maxx<imgSize[1] and maxy<imgSize[0]:
            widImg=img[miny:maxy,minx:maxx]
            
        return widImg

    def getWindowImgs(self, objImg, tmpImg, resiImg, poslist, size):
        
        objPath = "%s/%s"%(self.tmpDir, objImg)
        tmpPath = "%s/%s"%(self.tmpDir, tmpImg)
        resiPath = "%s/%s"%(self.tmpDir, resiImg)
        
        objData = fits.getdata(objPath)
        tmpData = fits.getdata(tmpPath)
        resiData = fits.getdata(resiPath)
        
        subImgs = []
        for tpos in poslist:
            objWid = self.getWindowImg(objData, (tpos[0], tpos[1]), size)
            tmpWid = self.getWindowImg(tmpData, (tpos[2], tpos[3]), size)
            resiWid = self.getWindowImg(resiData, (tpos[4], tpos[5]), size)
            
            subImgs.append([objWid, tmpWid, resiWid])
                
        return subImgs
    
    
    def simFOT(self, oImg, tImg):
        
        self.objTmpResi = self.runHotpants(self.objectImg, self.templateImg)
        
        #sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','1','-ANALYSIS_THRESH','1']
        #self.objTmpResiCat = self.runSextractor(self.objTmpResi, sexConf)
        self.objTmpResiCat = self.runSextractor(self.objTmpResi)
        
        #过滤“真OT”，如小行星等
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.objTmpResiCat, self.obj_tmp_cn5, self.r5)
        otr_otcn5_cn5 = nmhFile
        otr_otcn5_cn5f = filtOTs(otr_otcn5_cn5, self.tmpDir)
        
        mchFile1, nmhFile1, mchPair1 = self.runCrossMatch(otr_otcn5_cn5f, self.osn5, self.r5)
        mchFile2, nmhFile2, mchPair2 = self.runCrossMatch(otr_otcn5_cn5f, self.tsn5, self.r5)
        
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair1)).astype(np.int)
        tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair2)).astype(np.int)
        tIdx1 = tIdx1 - 1
        tIdx2 = tIdx2 - 1
        self.log.debug("objectCat matched data %d, templateCat matched data %d"%(len(tIdx1), len(tIdx2)))
        
        #unionIdx = np.intersect1d(tIdx1[:,0], tIdx2[:,0])  #union1d
        #self.log.debug("intersect objectCat and templateCat matched data: %d"%(unionIdx.shape[0]))
        
        tnames1 = ['resiId','objId']
        tnames2 = ['resiId','tmpId']
        df1 = pd.DataFrame(data=tIdx1, columns=tnames1)
        df2 = pd.DataFrame(data=tIdx2, columns=tnames2)
        unionIdx=pd.merge(df1, df2, how='inner', on=['resiId'])
        self.log.debug("innerjoin objectCat and templateCat matched data %d"%(unionIdx.shape[0]))
        
        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, otr_otcn5_cn5f))
        tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, self.osn5))
        tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, self.tsn5))
        
        tdata11 = tdata2[unionIdx["objId"].values]
        tdata12 = tdata3[unionIdx["tmpId"].values]
        tdata22 = tdata1[unionIdx["resiId"].values]
        
        poslist = np.concatenate(([tdata11[:,3]], [tdata11[:,4]], [tdata12[:,3]], [tdata12[:,4]], [tdata22[:,0]], [tdata22[:,1]]), axis=0).transpose()
        
        #print(poslist)
        #genFinalOTDs9Reg('fot', self.tmpDir, poslist)
        
        size = self.subImgSize
        subImgBuffer = self.getWindowImgs(self.objectImg, self.templateImg, self.objTmpResi, poslist, size)
        objS2NBuffer = tdata22[:,3]
        
        self.log.info("\n******************")
        self.log.info("simulation False OT, total sub image %d"%(len(subImgBuffer)))
        
        subImgs = np.array(subImgBuffer)
        print(subImgs.shape)
        print(objS2NBuffer.shape)
        
        return subImgs, objS2NBuffer.flatten()
        

    def simTOT(self, oImg, tImg, subImgNum=100):
        
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, 24)
        self.osn32 = nmhFile

        osn16s = selectTempOTs(self.osn16, self.tmpDir)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, osn16s))
        if len(tdata.shape)<2 or tdata.shape[0]<100:
            print("%s has too little stars, break this run"%(oImg))
            return np.array([]), np.array([])
        
        osn16sf = filtOTs(osn16s, self.tmpDir)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, osn16sf))
        if len(tdata.shape)<2 or tdata.shape[0]<45:
            print("%s has too little stars, break this run"%(oImg))
            return np.array([]), np.array([])
        
        osn32f = filtOTs(self.osn32, self.tmpDir)
        
        mchFile, nmhFile, mchPair = self.runCrossMatch(osn32f, self.tsn5, self.r5)
        osn32s_tsn5_cm5 = mchFile
        osn32s_tsn5_cm5_pair = mchPair
        
        totalTOT = subImgNum
        subImgBuffer = []
        objS2NBuffer = []
        tnum = 0
        imgSimClass = ImageSimulation()
        
        ii = 1
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        while tnum<totalTOT:
            simFile, simPosFile, simDeltaXYA, tmpOtImgs = imgSimClass.simulateImage1(osn32f, self.objectImg, osn16sf, self.objectImg)
            
            outpre= self.objectImgOrig.split(".")[0]
            preViewPath = "%s/%s_psf.jpg"%(self.preViewDir, outpre)
            if not os.path.exists(preViewPath):
                psfView = genPSFView(tmpOtImgs)
                Image.fromarray(psfView).save(preViewPath)
            
            self.objectImgSim = simFile
            self.objectImgSimAdd = simPosFile
            
            self.simTmpResi = self.runHotpants(self.objectImgSim, self.templateImg)
            self.simTmpResiCat = self.runSextractor(self.simTmpResi, sexConf)
            
            simTmpResiCatEf = filtByEllipticity(self.simTmpResiCat, self.tmpDir, maxEllip=0.5)
            mchFile, nmhFile = self.runSelfMatch(simTmpResiCatEf, self.r5)
            simTmpResiCatEf_sn32 = nmhFile
            #simTmpResiCatEf_sn32 = simTmpResiCatEf
            
            mchFile, nmhFile, mchPair = self.runCrossMatch(self.objectImgSimAdd, simTmpResiCatEf_sn32, self.r5)
            str_oisa_cm5 = mchFile
            str_oisa_cm5_pair = mchPair
            
            
            tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, osn32s_tsn5_cm5_pair)).astype(np.int)
            tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, str_oisa_cm5_pair)).astype(np.int)
            tIdx1 = tIdx1 - 1
            tIdx2 = tIdx2 - 1
            self.log.debug("objectCat matched data %d, ResiCat matched data %d"%(tIdx1.shape[0], tIdx2.shape[0]))
                    
            tnames1 = ['objId', 'tmpId']
            tnames2 = ['objId', 'resiId']
            
            #unionIdx = np.intersect1d(tIdx1[:,0], tIdx2[:,0])  #union1d
            #self.log.debug("intersect objectCat and templateCat matched data: %d"%(unionIdx.shape[0]))
            
            df1 = pd.DataFrame(data=tIdx1, columns=tnames1)
            df2 = pd.DataFrame(data=tIdx2, columns=tnames2)
            unionIdx=pd.merge(df1, df2, how='inner', on=['objId'])
            self.log.debug("innerjoin objectCat and templateCat matched data %d"%(unionIdx.shape[0]))
            
            tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, self.objectImgSimAdd))
            tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, self.tsn5))
            tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, simTmpResiCatEf_sn32))
            
            simDeltaXYA = np.array(simDeltaXYA)
            tdeltaXYA = simDeltaXYA[unionIdx["objId"].values]
            tdata11 = tdata1[unionIdx["objId"].values]
            tdata12 = tdata2[unionIdx["tmpId"].values]
            tdata22 = tdata3[unionIdx["resiId"].values]
            
            poslist = np.concatenate(([tdata11[:,0]], [tdata11[:,1]], 
                                      [tdata12[:,3]+tdeltaXYA[:,0]], [tdata12[:,4]+tdeltaXYA[:,1]], 
                                      [tdata22[:,0]], [tdata22[:,1]]), axis=0).transpose()
            #print(poslist)
            #genFinalOTDs9Reg('tot', self.tmpDir, poslist)
            size = self.subImgSize
            subImgs = self.getWindowImgs(self.objectImgSim, self.templateImg, self.simTmpResi, poslist, size)
            tnum = tnum + len(subImgs)
            
            subImgBuffer.extend(subImgs)
            objS2NBuffer.extend(tdata22[:,3].tolist())
            
            self.log.info("\n******************")
            self.log.info("run %d, total sub image %d"%(ii, tnum))
            if ii>6:
                break
            ii = ii + 1
            #break
        
        subImgs = np.array(subImgBuffer)
        objS2NBuffer = np.array(objS2NBuffer)
        print(subImgs.shape)
        print(objS2NBuffer.shape)
        
        return subImgs, objS2NBuffer
    
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
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r5)
        self.osn5 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.templateImgCat, self.r5)
        self.tsn5 = nmhFile
        
        #pickle
        oImgPre = oImg[:oImg.index(".")]
        totpath = '%s/%s_otimg_tot.npz'%(self.destDir, oImgPre)
        fotpath = '%s/%s_otimg_fot.npz'%(self.destDir, oImgPre)
        if not os.path.exists(fotpath):
            simFOTs, s2nf = self.simFOT(self.objectImg, self.templateImg)
            np.savez_compressed(fotpath, fot=simFOTs, fs2n=s2nf)
        else:
            tdata1 = np.load(fotpath)
            simFOTs = tdata1['fot']
            print("read %d false OT from %s"%(simFOTs.shape[0], fotpath))
            
        simTOTs, s2nt = self.simTOT(self.objectImg, self.templateImg, simFOTs.shape[0])
        np.savez_compressed(totpath, tot=simTOTs, ts2n=s2nt)
        
        print("%s with TOT %d, FOT %d"%(oImg, simTOTs.shape[0], simFOTs.shape[0]))
        
        
    def testSimImage(self):
        
        objectImg = 'CombZ_0.fit'
        templateImg = 'CombZ_temp.fit'
        self.simImage(objectImg, templateImg)
    
    def test(self):
                    
        oImg = 'CombZ_0.fit'
        tImg = 'CombZ_temp.fit'
        
        os.system("rm -rf %s/*"%(self.tmpDir))
                
        os.system("cp %s/%s %s/%s"%(self.srcDir, oImg, self.tmpDir, self.objectImg))
        os.system("cp %s/%s %s/%s"%(self.srcDir, tImg, self.tmpDir, self.templateImg))
        
        self.objectImgCat = self.runSextractor(self.objectImg)
        self.templateImgCat = self.runSextractor(self.templateImg)
        #查找“真OT”，如小行星等
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.objectImgCat, self.templateImgCat, self.r5)
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.objectImgCat, self.objectImgCat, 1)
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.templateImgCat, self.templateImgCat, 1)
    
    def batchSim(self):
        
        # ls CombZ_*fit
        templateImg = 'CombZ_temp.fit'
        flist = os.listdir(self.srcDir)
        flist.sort()
        
        imgs = []
        for tfilename in flist:
            if tfilename.find("fit")>-1:
                imgs.append(tfilename)
        
        print("total %d images"%(len(imgs)))
        for i, timg in enumerate(imgs):
            if i > 59 and i< 600:
                
                tIdx = i - 50
                templateImg = imgs[tIdx]
                print("\n\nprocess %d %s, template is %d %s"%(i, timg, tIdx, templateImg))
                self.simImage(timg, templateImg)
                
                thumbnail = getThumbnail(self.srcDir, timg, stampSize=(100,100), grid=(5, 5), innerSpace = 1)
                thumbnail = scipy.ndimage.zoom(thumbnail, 4, order=0)
                
                outpre= timg.split(".")[0]
                thumbnailPath = "%s/%s_thb.jpg"%(self.preViewDir, outpre)
                Image.fromarray(thumbnail).save(thumbnailPath)
        
                #break
            
if __name__ == "__main__":
    
    otsim = OTSimulation()
    otsim.batchSim()
    #otsim.testSimImage()
    #otsim.simFOT2('obj', 'tmp')
    