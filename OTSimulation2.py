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
from gwac_util import zscale_image, selectTempOTs, filtOTs, filtByEllipticity, genFinalOTDs9Reg, polyfit2d, polyval2d
from imgSim import ImageSimulation

class OTSimulation2(object):
    def __init__(self):
        
        self.verbose = True
        
        self.varDir = "/home/xy/Downloads/myresource/deep_data2/simulate_tools"
        self.srcDir = "/home/xy/Downloads/myresource/deep_data2/chaodata" # ls CombZ_*fit
        self.tmpDir="/run/shm/gwacsim"
        self.destDir="/home/xy/Downloads/myresource/deep_data2/simot/rest_data"
        self.matchProgram="/home/xy/program/netbeans/C/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"
        self.imgDiffProgram="/home/xy/program/C/hotpants/hotpants"
        self.mapProgram="/home/xy/program/netbeans/C/GWACProject/dist/Debug/GNU-Linux/gwacproject"
                
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
        
    def runGeoMap(self, pairsCat):
        
        objpre= pairsCat.split(".")[0]
        objFPath = "%s/%s"%(self.tmpDir, pairsCat)
        outFile = "%s_geomap.parm"%(objpre)
        outFPath = "%s/%s"%(self.tmpDir, outFile)
        
        order='5'
        iterNum='4'
        rejSigma='2.5'
        
        #exeprog geomap pairs.cat map_parm.txt order=5 iterNum=4 rejSigma=2.5
        cmd = [self.mapProgram, 'geomap', objFPath, outFPath, order, iterNum, rejSigma]
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        #self.log.info(stdoutstr)
        #self.log.info(stderrstr)
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run geomap success.")
            self.log.debug("generate geomap %s"%(outFPath))
        else:
            self.log.error("geomap failed.")
            
        return outFile
        
    def runGeoXytran(self, objCatalog, mapParmFile):
        
        objpre= objCatalog.split(".")[0]
        objFPath = "%s/%s"%(self.tmpDir, objCatalog)
        outFile = "%s_geoxytran.cat"%(objpre)
        outFPath = "%s/%s"%(self.tmpDir, outFile)
        mapParmFPath = "%s/%s"%(self.tmpDir, mapParmFile)
        
        direction='-1'
        
        #exeprog geoxytran data.cat mapParm.txt data.out direction=-1
        cmd = [self.mapProgram, 'geoxytran', objFPath, mapParmFPath, outFPath, direction]
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run geoxytran success.")
            self.log.debug("generate geoxytran %s"%(outFPath))
        else:
            self.log.error("geoxytran failed.")
            
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
        
    def simImage(self, oImg, tImg):
    
        os.system("rm -rf %s/*"%(self.tmpDir))
                
        os.system("cp %s/%s %s/%s"%(self.srcDir, oImg, self.tmpDir, self.objectImg))
        os.system("cp %s/%s %s/%s"%(self.srcDir, tImg, self.tmpDir, self.templateImg))
        
        self.objectImgCat = self.runSextractor(self.objectImg)
        self.templateImgCat = self.runSextractor(self.templateImg)
        
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r16)
        self.osn16 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.objectImgCat, self.r10)
        osn10 = nmhFile
        mchFile, nmhFile = self.runSelfMatch(self.templateImgCat, self.r10)
        tsn10 = nmhFile
        
        osn16s = selectTempOTs(self.osn16, self.tmpDir)
        osn16sf = filtOTs(osn16s, self.tmpDir)
        
        imgSimClass = ImageSimulation()
        simFile, simPosFile = imgSimClass.simulateImage2(self.objectImg, osn16sf, self.objectImg)
        
        simTmpResi = self.runHotpants(simFile, self.templateImg)
        simTmpResiCat = self.runSextractor(simTmpResi)
        mchFile, nmhFile = self.runSelfMatch(simTmpResiCat, self.r10)
        str_sn10 = nmhFile
        
        str_sn10f = filtOTs(str_sn10, self.tmpDir)
        osn10f = filtOTs(osn10, self.tmpDir)
        tsn10f = filtOTs(tsn10, self.tmpDir)
        
        mchFile1, nmhFile1, mchPair1 = self.runCrossMatch(str_sn10f, simPosFile, self.r5)
        str_sn10f_spf_cn5 = nmhFile1
        mchFile2, nmhFile2, mchPair2 = self.runCrossMatch(osn10f, tsn10f, self.r5)

        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair1)).astype(np.int)
        tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair2)).astype(np.int)

        tdata11 = np.loadtxt("%s/%s"%(self.tmpDir, str_sn10f))
        tdata12 = np.loadtxt("%s/%s"%(self.tmpDir, simPosFile))
        tdata21 = np.loadtxt("%s/%s"%(self.tmpDir, osn10f))
        tdata22 = np.loadtxt("%s/%s"%(self.tmpDir, tsn10f))
        
        print(str_sn10f_spf_cn5)
        print(mchPair1)
        print(mchPair2)
        
        print(str_sn10f)
        print(simPosFile)
        print(osn10f)
        print(tsn10f)
        
        
        
    def simImage2(self, oImg, tImg):
    
        str_sn10f_spf_cn5 = 'oi_sim4calib_ti_resi_sn10f_oi_sim4calib_pos_cn5.cat'
        mchPair1 = 'oi_sim4calib_ti_resi_sn10f_oi_sim4calib_pos_cm5.pair'
        mchPair2 = 'oi_sn10f_ti_sn10f_cm5.pair'
        
        str_sn10f = 'oi_sim4calib_ti_resi_sn10f.cat'
        simPosFile = 'oi_sim4calib_pos.cat'
        osn10f = 'oi_sn10f.cat'
        tsn10f = 'ti_sn10f.cat'

        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair1)).astype(np.int)
        tIdx2 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair2)).astype(np.int)
        tIdx1 = tIdx1 - 1
        tIdx2 = tIdx2 - 1
        print(tIdx1.shape)
        print(tIdx2.shape)

        tdata11 = np.loadtxt("%s/%s"%(self.tmpDir, str_sn10f))
        tdata12 = np.loadtxt("%s/%s"%(self.tmpDir, simPosFile))
        tdata21 = np.loadtxt("%s/%s"%(self.tmpDir, osn10f))
        tdata22 = np.loadtxt("%s/%s"%(self.tmpDir, tsn10f))
        
        print(tdata11.shape)
        print(tdata12.shape)
        print(tdata21.shape)
        print(tdata22.shape)
        
        resi2objCoorResi = tdata11[tIdx1[:,0]]
        resi2objCoorObj  = tdata12[tIdx1[:,1]]
        obj2tmpCoorObj   = tdata21[tIdx2[:,0]]
        obj2tmpCoorTmp   = tdata22[tIdx2[:,1]]
        
        ox1 = resi2objCoorResi[:,0]
        oy1 = resi2objCoorResi[:,1]
        tx1 = resi2objCoorObj[:,0]
        ty1 = resi2objCoorObj[:,1]
        
        print(ox1.shape)
        tfname1 = "resi2obj_pos_pair.cat"
        with open("%s/resi2obj_pos_pair.cat"%(self.tmpDir), 'w') as fp1:
            for i in range(len(ox1)):
                fp1.write("%.5f %.5f %.5f %.5f \n"%(ox1[i], oy1[i], tx1[i], ty1[i]))
                
        tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, tfname1))
        print(tdata3[:3])
        xResi = np.fabs(tdata3[:,0] - tdata3[:,2])
        yResi = np.fabs(tdata3[:,1] - tdata3[:,3])
        
        print(np.max(xResi))
        print(np.min(xResi))
        print(np.std(xResi))
        
        print(np.max(yResi))
        print(np.min(yResi))
        print(np.std(yResi))
        
        mapParmFile = self.runGeoMap(tfname1)
        txyTranFile = self.runGeoXytran(tfname1, mapParmFile)
        
        tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, txyTranFile))
        print(tdata3[:3])
        
        xResi = np.fabs(tdata3[:,0] - tdata3[:,2])
        yResi = np.fabs(tdata3[:,1] - tdata3[:,3])
        
        print(np.max(xResi))
        print(np.min(xResi))
        print(np.std(xResi))
        
        print(np.max(yResi))
        print(np.min(yResi))
        print(np.std(yResi))
        
        
        '''
        ox2 = obj2tmpCoorObj[:,0]
        oy2 = obj2tmpCoorObj[:,1]
        tx2 = obj2tmpCoorTmp[:,0]
        ty2 = obj2tmpCoorTmp[:,1]
        '''
        

        
        
    def testSimImage(self):
        
        if not os.path.exists(self.tmpDir):
            os.system("mkdir %s"%(self.tmpDir))
        
        objectImg = 'CombZ_0.fit'
        templateImg = 'CombZ_temp.fit'
        self.simImage2(objectImg, templateImg)
    
    def batchSim(self):
    
        if not os.path.exists(self.tmpDir):
            os.system("mkdir %s"%(self.tmpDir))
            
        flist = os.listdir(self.srcDir)
        flist.sort()
        for tfilename in flist:
            if tfilename.find("jpg")>-1:
                tpath = "%s/%s"%(self.srcDir, tfilename)
            
if __name__ == "__main__":
    
    otsim = OTSimulation2()
    otsim.testSimImage()
    #otsim.simFOT2('obj', 'tmp')
    