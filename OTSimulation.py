# -*- coding: utf-8 -*-
import cv2
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
from gwac_util import zscale_image, selectTempOTs, filtOTs, filtByEllipticity, genFinalOTDs9Reg
from imgSim import ImageSimulation


class OTSimulation(object):
    def __init__(self):
        
        self.verbose = True
        
        self.varDir = "/home/xy/Downloads/myresource/deep_data2/simulate_tools"
        self.srcDir = "/home/xy/Downloads/myresource/deep_data2/chaodata" # ls CombZ_*fit
        self.tmpDir="/run/shm/gwacsim"
        self.destDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data"
        self.matchProgram="/home/xy/program/netbeans/C/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"
        self.imgDiffProgram="/home/xy/program/C/hotpants/hotpants"
                
        if not os.path.exists(self.tmpDir):
            os.system("mkdir %s"%(self.tmpDir))
            
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
    def runSextractor(self, fname):
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(self.tmpDir, fname)
        outFile = "%s.cat"%(outpre)
        outFPath = "%s/%s"%(self.tmpDir, outFile)
        cnfPath = "%s/config/OTsearch.sex"%(self.varDir)
        
        # run sextractor from the unix command line
        cmd = ['sex', fullPath, '-c', cnfPath, '-CATALOG_NAME', outFPath]
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
        
        i = 0
        subImgs = []
        for tpos in poslist:
            objWid = self.getWindowImg(objData, (tpos[0], tpos[1]), size)
            tmpWid = self.getWindowImg(tmpData, (tpos[2], tpos[3]), size)
            resiWid = self.getWindowImg(resiData, (tpos[4], tpos[5]), size)
            
            if len(resiWid)>0 and len(objWid)>0 and len(tmpWid)>0:
                
                #self.log.debug(tpos)
                
                #cv2.circle(img, center, radius, color, thickness=1, lineType=8, shift=0)
                #cv2.circle(objWid,(int(size/2),int(size/2)),2,(255,0,0),1)
                #cv2.circle(tmpWid,(int(size/2),int(size/2)),2,(255,0,0),1)
                #cv2.circle(resiWid,(int(size/2),int(size/2)),2,(255,0,0),1)
                
                objWidz = zscale_image(objWid)
                tmpWidz = zscale_image(tmpWid)
                resiWidz = zscale_image(resiWid)
                subImgs.append([objWidz, tmpWidz, resiWidz])
                
                #conWid = np.concatenate((objWidz, tmpWidz, resiWidz), axis=1)
                #plt.imshow(conWid, cmap='gray')
                #plt.show()
                i = i+1
                #if i>20:
                #    break
                
        return subImgs
    
    
    def simFOT(self, oImg, tImg):
        
        self.objTmpResi = self.runHotpants(self.objectImg, self.templateImg)
        self.objTmpResiCat = self.runSextractor(self.objTmpResi)
        
        #过滤“真OT”，如小行星等
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.objTmpResiCat, self.obj_tmp_cn5, self.r5)
        otr_otcn5_cn5 = nmhFile
        otr_otcn5_cn5f = filtOTs(otr_otcn5_cn5, self.tmpDir)
        
        mchFile1, nmhFile1, mchPair1 = self.runCrossMatch(otr_otcn5_cn5f, self.osn5, self.r5)
        mchFile2, nmhFile2, mchPair2 = self.runCrossMatch(otr_otcn5_cn5f, self.tsn5, self.r5)
        
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair1)).astype(np.int)
        tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair2)).astype(np.int)
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
        
        self.log.info("\n******************")
        self.log.info("simulation False OT, total sub image %d"%(len(subImgBuffer)))
        
        rsts = np.array(subImgBuffer)
        print(rsts.shape)
        
        return rsts
        
    def simFOT2(self, oImg, tImg):
                      
        mchPair1 = 'oi_ti_resi_oi_ti_cn5_cn5f_oi_sn5_cm5.pair'
        mchPair2 = 'oi_ti_resi_oi_ti_cn5_cn5f_ti_sn5_cm5.pair'
        
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair1)).astype(np.int)
        tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair2)).astype(np.int)
        self.log.debug("objectCat matched data %d, templateCat matched data %d"%(tIdx1.shape[0], tIdx2.shape[0]))
                
        tnames1 = ['resiId','objId']
        tnames2 = ['resiId','tmpId']
        
        #unionIdx = np.intersect1d(tIdx1[:,0], tIdx2[:,0])  #union1d
        #self.log.debug("intersect objectCat and templateCat matched data: %d"%(unionIdx.shape[0]))
        
        df1 = pd.DataFrame(data=tIdx1, columns=tnames1)
        df2 = pd.DataFrame(data=tIdx2, columns=tnames2)
        unionIdx=pd.merge(df1, df2, how='inner', on=['resiId'])
        
        otr_otcn5_cn5f = 'oi_ti_resi_oi_ti_cn5_cn5f.cat'
        self.osn5 = 'oi_sn5.cat'
        self.tsn5 = 'ti_sn5.cat'
        
        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, otr_otcn5_cn5f))
        tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, self.osn5))
        tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, self.tsn5))
        
        tdata11 = tdata2[unionIdx["objId"].values]
        tdata12 = tdata3[unionIdx["tmpId"].values]
        tdata22 = tdata1[unionIdx["resiId"].values]
        
        poslist = np.concatenate(([tdata11[:,3]], [tdata11[:,4]], [tdata12[:,3]], [tdata12[:,4]], [tdata22[:,0]], [tdata22[:,1]]), axis=0).transpose()
        #print(poslist)
        
        size = 100
        resiImg = 'oi_ti_resi.fit'
        objImg = 'oi.fit'
        tmpImg = 'ti.fit'
        self.getWindowImgs(objImg, tmpImg, resiImg, poslist, size)

    def simTOT(self, oImg, tImg, subImgNum=100):
        
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, 24)
        self.osn32 = nmhFile

        osn16s = selectTempOTs(self.osn16, self.tmpDir)
        osn16sf = filtOTs(osn16s, self.tmpDir)
        osn32f = filtOTs(self.osn32, self.tmpDir)
        
        mchFile, nmhFile, mchPair = self.runCrossMatch(osn32f, self.tsn5, self.r5)
        osn32s_tsn5_cm5 = mchFile
        osn32s_tsn5_cm5_pair = mchPair
        
        totalTOT = subImgNum
        subImgBuffer = []
        tnum = 0
        imgSimClass = ImageSimulation()
        
        ii = 1
        while tnum<totalTOT:
            simFile, simPosFile, simDeltaXYA = imgSimClass.simulateImage1(osn32f, self.objectImg, osn16sf, self.objectImg)
            self.objectImgSim = simFile
            self.objectImgSimAdd = simPosFile
            
            self.simTmpResi = self.runHotpants(self.objectImgSim, self.templateImg)
            self.simTmpResiCat = self.runSextractor(self.simTmpResi)
            
            simTmpResiCatEf = filtByEllipticity(self.simTmpResiCat, self.tmpDir, maxEllip=0.2)
            mchFile, nmhFile = self.runSelfMatch(simTmpResiCatEf, self.r32)
            simTmpResiCatEf_sn32 = nmhFile
            
            mchFile, nmhFile, mchPair = self.runCrossMatch(self.objectImgSimAdd, simTmpResiCatEf_sn32, self.r5)
            str_oisa_cm5 = mchFile
            str_oisa_cm5_pair = mchPair
            
            
            tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, osn32s_tsn5_cm5_pair)).astype(np.int)
            tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, str_oisa_cm5_pair)).astype(np.int)
            self.log.debug("objectCat matched data %d, templateCat matched data %d"%(tIdx1.shape[0], tIdx2.shape[0]))
                    
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
            
            self.log.info("\n******************")
            self.log.info("run %d, total sub image %d"%(ii, tnum))
            ii = ii + 1
        
        rsts = np.array(subImgBuffer)
        print(rsts.shape)
        
        return rsts
    
    def simTOT2(self, oImg, tImg, totalSubImgNum=100):
        
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, 24)
        self.osn32 = nmhFile

        osn16s = selectTempOTs(self.osn16, self.tmpDir)
        osn16sf = filtOTs(osn16s, self.tmpDir)
        osn32f = filtOTs(self.osn32, self.tmpDir)
        
        mchFile, nmhFile, mchPair = self.runCrossMatch(osn32f, self.tsn5, self.r5)
        osn32s_tsn5_cm5 = mchFile
        osn32s_tsn5_cm5_pair = mchPair
        
        subImgBuffer = []
        
        imgSimClass = ImageSimulation()
        simFile, simPosFile, simDeltaXYA = imgSimClass.simulateImage3(osn32f, self.objectImg, osn16sf, self.objectImg, totalSubImgNum)
        self.objectImgSim = simFile
        
        print("before filter %d"%(len(simDeltaXYA)))
        mchFile, nmhFile = self.runSelfMatch(simPosFile, self.r5)
        self.objectImgSimAdd = nmhFile
        
        tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, nmhFile))
        print("after filter %d"%(tdata1.shape[0]))
        
        self.simTmpResi = self.runHotpants(self.objectImgSim, self.templateImg)
        self.simTmpResiCat = self.runSextractor(self.simTmpResi)
        
        simTmpResiCatEf = filtByEllipticity(self.simTmpResiCat, self.tmpDir, maxEllip=0.2)
        mchFile, nmhFile = self.runSelfMatch(simTmpResiCatEf, self.r32)
        simTmpResiCatEf_sn32 = nmhFile
        
        mchFile, nmhFile, mchPair = self.runCrossMatch(self.objectImgSimAdd, simTmpResiCatEf_sn32, self.r5)
        str_oisa_cm5 = mchFile
        str_oisa_cm5_pair = mchPair
        
        
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, osn32s_tsn5_cm5_pair)).astype(np.int)
        tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, str_oisa_cm5_pair)).astype(np.int)
        self.log.debug("objectCat matched data %d, templateCat matched data %d"%(tIdx1.shape[0], tIdx2.shape[0]))
                
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
        subImgBuffer = self.getWindowImgs(self.objectImgSim, self.templateImg, self.simTmpResi, poslist, size)
        
        self.log.info("\n******************")
        self.log.info("simulation True OT, total sub image %d"%(len(subImgBuffer)))
        
        rsts = np.array(subImgBuffer)
        print(rsts.shape)
        
        return rsts
        
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
        
        
        simFOTs = self.simFOT(self.objectImg, self.templateImg)
        simTOTs = self.simTOT(self.objectImg, self.templateImg, simFOTs.shape[0])
        
        print("%s with TOT %d, FOT %d"%(oImg, simTOTs.shape[0], simFOTs.shape[0]))
        
        #pickle
        oImgPre = oImg[:oImg.index(".")]
        tpath = '%s/%s_otimg.npz'%(self.destDir, oImgPre)
        np.savez_compressed(tpath, tot=simTOTs, fot=simFOTs)
        
        
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
            if tfilename.find("fit")>-1 and tfilename.find("temp")==-1:
                imgs.append(tfilename)
                
        for timg in imgs:
            print("\n\nprocess %s"%(timg))
            self.simImage(timg, templateImg)
            #break
            
if __name__ == "__main__":
    
    otsim = OTSimulation()
    otsim.batchSim()
    #otsim.testSimImage()
    #otsim.simFOT2('obj', 'tmp')
    