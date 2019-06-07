# -*- coding: utf-8 -*-
import numpy as np
import os
import sys
import math
import time
import subprocess
from datetime import datetime
import traceback
from PIL import Image
import scipy.ndimage
from astropy.wcs import WCS
from astropy.time import Time
from astropy.io import fits

from gwac_util import getThumbnail, genPSFView, getWindowImgs, getLastLine, selectTempOTs, filtOTs, filtByEllipticity, getDs9Reg
from imgSim import ImageSimulation
from astrotools import AstroTools
            
class BatchImageSim(object):
    def __init__(self, dataRoot, dataDest, tools, camName, skyName): 
        
        self.camName = camName
        self.skyName = str(skyName)
        self.ffNumber = 0
        self.toolPath = os.getcwd()
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim2"
        self.tmpUpload="/dev/shm/gwacupload"
        self.tmpDir="%s/tmp"%(self.tmpRoot)
        self.tmpCat="%s/cat"%(self.tmpRoot)
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        self.modelPath="%s/tools/mlmodel"%(self.toolPath)
        
        #self.dataRoot = "/data/gwac_data"
        self.srcDir0 = "%s"%(dataRoot)
        self.srcDir = "%s"%(dataRoot)
            
        self.objectImg = 'oi.fit'
        self.templateImg = 'ti.fit'
        self.objectImgSim = 'ois.fit'
        self.objTmpResi = 'otr.fit'
        self.simTmpResi = 'str.fit'
        self.newImageName = "new.fit"
        
        self.badPixCat = 'badpix.cat'
        self.objectImgSimAdd = 'oisa.cat'
        self.objectImgCat = 'oi.cat'
        self.templateImgCat = 'ti.cat'
        self.objectImgSimCat = 'ois.cat'
        self.objTmpResiCat = 'otr.cat'
        self.simTmpResiCat = 'str.cat'
        
        self.imgSize = (4136, 4096)
        self.subImgSize = 21
        self.imgShape = []  
             
        self.selTemplateNum = 10 # 10 3
        self.maxFalseNum = 5
        
        self.tools = tools
        self.log = tools.log
        
        self.initReg(0)
                
        
        self.dCatDir="%s/dcats"%(dataDest)
        self.simFitsDir="%s/simFits"%(dataDest)
        self.alignFitsDir="%s/alignFits"%(dataDest)
        self.alignCatsDir="%s/alignCats"%(dataDest)
        self.resiFitDir="%s/resiFit"%(dataDest)
        self.resiCatDir="%s/resiCat"%(dataDest)
        self.preViewDir="%s/preview"%(dataDest)
        self.preViewSimResiDir="%s/previewSimResi"%(dataDest)
        self.simCatAddDir="%s/simCatAdd"%(dataDest)
    
        if not os.path.exists(self.dCatDir):
            os.system("mkdir -p %s"%(self.dCatDir))
        if not os.path.exists(self.simFitsDir):
            os.system("mkdir -p %s"%(self.simFitsDir))
        if not os.path.exists(self.alignFitsDir):
            os.system("mkdir -p %s"%(self.alignFitsDir))
        if not os.path.exists(self.alignCatsDir):
            os.system("mkdir -p %s"%(self.alignCatsDir))
        if not os.path.exists(self.resiFitDir):
            os.system("mkdir -p %s"%(self.resiFitDir))
        if not os.path.exists(self.resiCatDir):
            os.system("mkdir -p %s"%(self.resiCatDir))
        if not os.path.exists(self.preViewDir):
            os.system("mkdir -p %s"%(self.preViewDir))
        if not os.path.exists(self.preViewSimResiDir):
            os.system("mkdir -p %s"%(self.preViewSimResiDir))
        if not os.path.exists(self.simCatAddDir):
            os.system("mkdir -p %s"%(self.simCatAddDir))

    def sendMsg(self, tmsg):
        
        tmsgStr = "%s, sky:%s, ffNum:%d\n %s"%(self.camName, self.skyName, self.ffNumber, tmsg)
        self.tools.sendTriggerMsg(tmsgStr)
    
    def initReg(self, idx):
        
        if idx<=0:
            idx =0
            os.system("rm -rf %s/*"%(self.tmpRoot))
            os.system("rm -rf %s/*"%(self.tmpUpload))
            if not os.path.exists(self.tmpUpload):
                os.system("mkdir -p %s"%(self.tmpUpload))
            if not os.path.exists(self.templateDir):
                os.system("mkdir -p %s"%(self.templateDir))
            if not os.path.exists(self.tmpDir):
                os.system("mkdir -p %s"%(self.tmpDir))
            if not os.path.exists(self.tmpCat):
                os.system("mkdir -p %s"%(self.tmpCat))
        
        self.procNum = 0
        self.tmplImgIdx = 0 
        self.regFalseNum = 0
        self.regSuccessNum = 0
        self.diffFalseNum = 0
        self.origTmplImgName = ""
        self.regFalseIdx = 0
        self.makeTempFalseNum = 0
        self.imglist = []
        self.transHGs = []
        
    
    def getPosXY(self, srcDir, fileName):
        
        tdata = np.loadtxt("%s/%s"%(srcDir, fileName))
        txy = tdata[:,0:2]
        
        tpre= fileName.split(".")[0]
        saveName = "%s_objxy.cat"%(tpre)
        savePath = "%s/%s"%(srcDir, saveName)
        np.savetxt(savePath, txy, fmt='%.5f',delimiter=' ')
        
        return saveName
        
    def savePosXY(self, srcDir, fileName, posXY):
        
        tdata1 = np.loadtxt("%s/%s"%(srcDir, fileName))
        tdata2 = np.loadtxt("%s/%s"%(srcDir, posXY))
        tdata1[:,0] = tdata2[:,0]
        tdata1[:,1] = tdata2[:,1]
        
        tpre= fileName.split(".")[0]
        saveName = "%s_trans.cat"%(tpre)
        savePath = "%s/%s"%(srcDir, saveName)
        np.savetxt(savePath, tdata1, fmt='%.5f',delimiter=' ')
        
        return saveName
    
    def reSaveData(self, tpath):
        tdata1 = np.loadtxt(tpath)
        tdata2 = tdata1[:,2:4]
        
        np.savetxt(tpath, tdata2, fmt='%.5f',delimiter=' ')
        
    def catTrans(self, objCat):
        
        tpre= objCat.split(".")[0]
        saveName1 = "%s_objsky.cat"%(tpre)
        saveName2 = "%s_tmptxy.cat"%(tpre)
        
        objCatXY = self.getPosXY(self.tmpDir, objCat)
        
        fitsPath = "%s/%s"%(self.tmpDir, self.objectImg)
        catInPath = "%s/%s"%(self.tmpDir, objCatXY)
        catOutPath = "%s/%s"%(self.tmpDir, saveName1)
        
        #tnx2sky <path of fits> <input file> <output file>
        cmd = ['tnx2sky', fitsPath, catInPath, catOutPath]
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        
        if os.path.exists(catOutPath) and status==0:
            self.log.debug("cat align success.")
            self.log.debug("generate aligned file1 %s"%(saveName1))
        else:
            self.log.error("cat align failed.")
        
        self.reSaveData(catOutPath)
        
        fitsPath2 = "%s/%s"%(self.tmpDir, self.templateImg)
        catOutPath2 = "%s/%s"%(self.tmpDir, saveName2)
        
        #tnx2sky <path of fits> <input file> <output file>
        cmd = ['tnx2xy', fitsPath2, catOutPath, catOutPath2]
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        
        if os.path.exists(catOutPath2) and status==0:
            self.log.debug("cat align success.")
            self.log.debug("generate aligned file1 %s"%(saveName2))
        else:
            self.log.error("cat align failed.")
            
        self.reSaveData(catOutPath2)
        transFile = self.savePosXY(self.tmpDir, objCat, saveName2)
        
        return transFile
            
    def getCats(self, srcDir, destDir):
        
        self.srcDir = srcDir
        self.dCatDir = destDir
        
        try:
            tfiles0 = os.listdir(self.srcDir)
            tfiles0.sort()
            
            tfiles = []
            for tfile in tfiles0:
                if tfile.find('mon_objt_190116')>0:
                    tfiles.append(tfile[:33])
            
            for i, imgName in enumerate(tfiles):
                
                starttime = datetime.now()
                tStr = "start sextractor %d: %s"%(i, imgName)
                self.log.info(tStr)
                
                os.system("rm -rf %s/*"%(self.tmpDir))
                imgpre= imgName.split(".")[0]
                catName = "%s.cat"%(imgpre)
                destCatFullPath = "%s/%s"%(self.dCatDir, catName)
                if os.path.exists(destCatFullPath):
                    self.log.info("%s.fit already cated, skip"%(imgpre))
                    continue
                
                oImgf = "%s/%s.fit"%(self.srcDir,imgpre)
                oImgfz = "%s/%s.fit.fz"%(self.srcDir,imgpre)
                if os.path.exists(oImgf):
                    os.system("cp %s/%s.fit %s/%s"%(self.srcDir, imgpre, self.tmpDir, self.objectImg))
                elif os.path.exists(oImgfz):
                    os.system("cp %s/%s.fit.fz %s/%s.fz"%(self.srcDir, imgpre, self.tmpDir, self.objectImg))
                    os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, self.objectImg))
                else:
                    self.log.warning("%s not exist"%(imgName))
                    continue
            
                        
                #self.tools.removeHeaderAndOverScan(self.tmpDir,self.objectImg)
        
                sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
                #sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
                fpar='sex_diff.par'
                self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf)
                os.system("cp %s/%s %s/%s"%(self.tmpDir, self.objectImgCat, self.dCatDir, catName))
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("start sextractor: %s use %d seconds"%(imgName, runTime))
                
                #if i>30:
                #    break
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
            
    def imgAlign(self):
        
        try:
            tfiles0 = os.listdir(self.srcDir)
            tfiles0.sort()
            
            tfiles = []
            for tfile in tfiles0:
                if tfile.find('mon_objt_190116')>0:
                    tfiles.append(tfile[:33])
            
            os.system("rm -rf %s/*"%(self.templateDir))
            tmpImgName = tfiles[0]
            tStr= tmpImgName.split(".")[0]
            os.system("cp %s/%s.cat %s/%s"%(self.dCatDir, tStr, self.templateDir, self.templateImgCat))
            os.system("cp %s/%s %s/%s"%(self.srcDir, tmpImgName, self.templateDir, self.templateImg))
            mchFile16, nmhFile16 = self.tools.runSelfMatch(self.templateDir, self.templateImgCat, 16)
            tmpt16 = nmhFile16
            
            os.system("cp %s/%s %s/%s.cat"%(self.templateDir, self.templateImgCat, self.alignCatsDir, tStr))
            os.system("cp %s/%s %s/%s.fit"%(self.templateDir, self.templateImg, self.alignFitsDir, tStr))
            
            tmplFieldId = fits.getval("%s/%s"%(self.templateDir, self.templateImg), 'FIELD_ID', 0) #getval getheader getdata
            
            for i, imgName in enumerate(tfiles[1:]):
                
                #if i<460:
                #    continue
                
                starttime = datetime.now()
                self.log.info("align %d: %s"%(i, imgName))
                
                os.system("rm -rf %s/*"%(self.tmpDir))
                imgpre= imgName.split(".")[0]
                tobjFitsFullPath = "%s/%s.fit"%(self.srcDir, imgpre)
                tobjCatsFullPath = "%s/%s.cat"%(self.dCatDir, imgpre)
                if (not os.path.exists(tobjFitsFullPath)) or (not os.path.exists(tobjCatsFullPath)):
                    self.log.error("%s (.fit or .cat) not exist, stop"%(imgpre))
                    break
                
                if os.path.exists("%s/%s.fit"%(self.alignFitsDir, imgpre)):
                    self.log.info("%s.fit already aligned, skip"%(imgpre))
                    continue
                
                os.system("cp %s/%s.fit %s/%s"%(self.srcDir, imgpre, self.tmpDir, self.objectImg))
                os.system("cp %s/%s.cat %s/%s"%(self.dCatDir, imgpre, self.tmpDir, self.objectImgCat))
                os.system("cp %s/%s %s/%s"%(self.templateDir, tmpt16, self.tmpDir, tmpt16))
                os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
                
                
                objFieldId = fits.getval("%s/%s"%(self.tmpDir, self.objectImg), 'FIELD_ID', 0) #getval getheader getdata
                if tmplFieldId!=objFieldId:
                    self.log.info("template %s fieldId different with object %s, skip"%(tmpImgName, imgName))
                    continue
                
                mchFile16, nmhFile16 = self.tools.runSelfMatch(self.tmpDir, self.objectImgCat, 16)
                obj16 = nmhFile16
            
                objTrans = self.catTrans(obj16)
                '''
                mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, objTrans, tmpt16, 5)
                transHG, xshift, yshift, xrms, yrms = self.tools.getMatchPosHmg(self.tmpDir, obj16, tmpt16, mchPair)
                '''
                transHG, xshift, yshift, xrms, yrms = self.tools.getMatchPosHmg2(self.tmpDir, obj16, objTrans)
                objImgAlign, objCatAlign = self.tools.imageAlignHmg(self.tmpDir, self.objectImg, self.objectImgCat, transHG)
                
                self.log.info("homography astrometry pos transform, xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
                        
                os.system("cp %s/%s %s/%s.fit"%(self.tmpDir, objImgAlign, self.alignFitsDir, imgpre))
                os.system("cp %s/%s %s/%s.cat"%(self.tmpDir, objCatAlign, self.alignCatsDir, imgpre))
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("align: %s use %d seconds"%(imgName, runTime))
                
                #break
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
            
              
    def imgDiff(self, srcDir, destDir):
        
        self.alignFitsDir = srcDir
        self.resiFitDir = destDir
        
        try:
            tfiles0 = os.listdir(self.alignFitsDir)
            tfiles0.sort()
            
            tfiles = []
            for tfile in tfiles0:
                if tfile.find('mon_objt_190116')>0:
                    tfiles.append(tfile[:33])
            
            os.system("rm -rf %s/*"%(self.templateDir))
            tmpImgName = tfiles[0]
            os.system("cp %s/%s %s/%s"%(self.alignFitsDir, tmpImgName, self.templateDir, self.templateImg))
            
            for i, imgName in enumerate(tfiles[1:]):

                if i%50!=1 and i<len(tfiles)-3:                
                    continue
                
                starttime = datetime.now()
                self.log.info("diff %d: %s"%(i, imgName))
                
                os.system("rm -rf %s/*"%(self.tmpDir))
                imgpre= imgName.split(".")[0]
                tobjFitsFullPath = "%s/%s.fit"%(self.alignFitsDir, imgpre)
                if not os.path.exists(tobjFitsFullPath):
                    self.log.error("%s.fit not exist, stop"%(imgpre))
                    break
                
                if os.path.exists("%s/%s.fit"%(self.resiFitDir, imgpre)):
                    self.log.info("%s.fit already diffed, skip"%(imgpre))
                    continue
                
                os.system("cp %s/%s.fit %s/%s"%(self.alignFitsDir, imgpre, self.tmpDir, self.objectImg))
                os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
                
                self.objTmpResi, runSuccess = self.tools.runHotpants(self.objectImg, self.templateImg, self.tmpDir)
                if not runSuccess:
                    self.log.info("%s.fit diff error..."%(imgpre))
                    continue
        
                os.system("cp %s/%s %s/%s.fit"%(self.tmpDir, self.objTmpResi, self.resiFitDir, imgpre))
        
                tgrid = 4
                tsize = 500
                tzoom = 2
                timg = getThumbnail(self.tmpDir, self.objTmpResi, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
                timg = scipy.ndimage.zoom(timg, tzoom, order=0)
                preViewPath = "%s/%s_resi.jpg"%(self.preViewDir, imgpre)
                Image.fromarray(timg).save(preViewPath)
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("diff: %s use %d seconds"%(imgName, runTime))
                
                #break
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)

    def magCali(self, objCat):
        
        tmpCat = "ucac4.mag"
        tmpCatP = "%s/%s"%(self.tmpDir, tmpCat)
        objCatP = "%s/%s"%(self.tmpDir, objCat)
        os.system("cp /data3/simulationTest/20190322/xlp/useful/ucac4.mag %s"%(tmpCatP))
        
        tdata1 = np.loadtxt(tmpCatP)
        np.savetxt(tmpCatP, tdata1[:,0:3], fmt='%.5f',delimiter=' ')
        
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, objCat, tmpCat, 1)
        
        tdata1 = np.loadtxt(objCatP)
        tdata2 = np.loadtxt(tmpCatP)
        tIdx1 = np.loadtxt("%s/%s"%(self.tmpDir, mchPair)).astype(np.int)
        tIdx1 = tIdx1 - 1
        
        tdata1 = tdata1[tIdx1[:,0]][:]
        tdata2 = tdata2[tIdx1[:,1]][:]
        tdata1[:,11] = tdata2[:,2]
        
        saveName = "%s_cali.cat"%(objCat.split(".")[0])
        np.savetxt("%s/%s"%(self.tmpDir, saveName), tdata1, fmt='%.5f',delimiter=' ')
        
        return saveName
    
    def imgSimulate(self, srcFitDir, destFitDir, destCatAddDir):
        
        try:
            tfiles0 = os.listdir(srcFitDir)
            tfiles0.sort()
            
            tfiles = []
            for tfile in tfiles0:
                if tfile.find('mon_objt_190116')>0:
                    tfiles.append(tfile[:33])
            
            tmpImgPath = "%s/%s"%(destFitDir, tfiles[0])
            if not os.path.exists(tmpImgPath):
                os.system("cp %s/%s %s"%(srcFitDir, tfiles[0], tmpImgPath))
            
            os.system("cp %s/%s %s/%s"%(srcFitDir, tfiles[0], self.templateDir, self.templateImg))
            
            sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']
            fpar='sex_diff.par'
            
            imgSimClass = ImageSimulation(self.tmpDir)
            for i, imgName in enumerate(tfiles[1:]):
                
                #if i<460:
                #    continue
                
                starttime = datetime.now()
                self.log.info("\n\n**********\nsimulate %d: %s"%(i, imgName))
                
                os.system("rm -rf %s/*"%(self.tmpDir))
                imgpre= imgName.split(".")[0]
                tobjFitsFullPath = "%s/%s.fit"%(srcFitDir, imgpre)
                if not os.path.exists(tobjFitsFullPath):
                    self.log.error("%s.fit not exist, stop"%(imgpre))
                    break
                
                if os.path.exists("%s/%s.fit"%(destFitDir, imgpre)):
                    self.log.info("%s.fit already simulated, skip"%(imgpre))
                    continue
                
                os.system("cp %s/%s.fit %s/%s"%(srcFitDir, imgpre, self.tmpDir, self.objectImg))
                
                #sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
                sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']
                self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf=sexConf)
                mchFile16, nmhFile16 = self.tools.runSelfMatch(self.tmpDir, self.objectImgCat, 16)
                self.osn16 = nmhFile16
                
                objCali = self.magCali(self.osn16)
                
                osn16s = selectTempOTs(objCali, self.tmpDir)
                tdata = np.loadtxt("%s/%s"%(self.tmpDir, osn16s))
                if len(tdata.shape)<2 or tdata.shape[0]<100:
                    self.log.error("%s has too little stars, break this run"%(self.objectImg))
                    continue
                
                osn16sf = filtOTs(osn16s, self.tmpDir)
                tdata = np.loadtxt("%s/%s"%(self.tmpDir, osn16sf))
                if len(tdata.shape)<2 or tdata.shape[0]<45:
                    self.log.error("%s has too little stars, break this run"%(self.objectImg))
                    continue
                
                mchFile, nmhFile = self.tools.runSelfMatch(self.tmpDir, self.objectImgCat, 24)
                self.osn32 = nmhFile
                osn32f = filtOTs(self.osn32, self.tmpDir)
                
                posmagFile="simAdd190324.cat"
                if i==0 or (not os.path.exists("%s/%s"%(self.templateDir, posmagFile))):
                    tposmagFile=""
                else:
                    tposmagFile=posmagFile
                    os.system("cp %s/%s %s/%s"%(self.templateDir, posmagFile, self.tmpDir, posmagFile))
                    
                simFile, simPosFile, tmpOtImgs = imgSimClass.simulateImage1(osn32f, self.objectImg, 
                                                                                         osn16sf, self.objectImg, posmagFile=tposmagFile)
                self.objectImgSim = simFile
                self.objectImgSimCatAdd = simPosFile
                
                #destFitDir, destCatAddDir
                os.system("cp %s/%s %s/%s.fit"%(self.tmpDir, self.objectImgSim, destFitDir, imgpre))
                os.system("cp %s/%s %s/%s.cat"%(self.tmpDir, self.objectImgSimCatAdd, destCatAddDir, imgpre))
                
                if i==0 or (not os.path.exists("%s/%s"%(self.templateDir,posmagFile))):
                    os.system("cp %s/%s %s/%s"%(self.tmpDir, self.objectImgSimCatAdd, self.templateDir, posmagFile))
                    
                if i%50==1 or i>=len(tfiles)-3:
                    
                    os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
                    self.simTmpResi, runSuccess = self.tools.runHotpants(self.objectImgSim, self.templateImg, self.tmpDir)
                    if not runSuccess:
                        self.log.info("%s.fit sim diff error..."%(imgpre))
                        continue
                    
                    sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
                    #self.objectImgSimCat = self.tools.runSextractor(self.objectImgSim, self.tmpDir, self.tmpDir, sexConf=sexConf)
                    self.simTmpResiCat = self.tools.runSextractor(self.simTmpResi, self.tmpDir, self.tmpDir, fpar, sexConf=sexConf)
                    
                    #simTmpResiCatEf = filtByEllipticity(self.simTmpResiCat, self.tmpDir, maxEllip=0.5)
                    #mchFile, nmhFile = self.tools.runSelfMatch(self.tmpDir, simTmpResiCatEf, 16)
                    #simTmpResiCatEf_sn32 = nmhFile
                    #simTmpResiCatEf_sn32 = simTmpResiCatEf
                    
                    #mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, self.objectImgSimCatAdd, simTmpResiCatEf, 5)
                    mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, self.objectImgSimCatAdd, self.simTmpResiCat, 5)
                    
                    tdata1 = np.loadtxt("%s/%s"%(self.tmpDir, self.objectImgSimCatAdd))
                    tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, self.simTmpResiCat))
                    tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
                    self.log.info("sim add %d, diff find %d, sim match diff %d, find percentage %.2f%%"%
                        (tdata1.shape[0], tdata2.shape[0],tdata3.shape[0],tdata3.shape[0]*100.0/tdata1.shape[0]))
                    os.system("cp %s/%s %s/%s_simResi.fit"%(self.tmpDir, self.simTmpResi, destFitDir, imgpre))
                    os.system("cp %s/%s %s/%s_simResi.cat"%(self.tmpDir, self.simTmpResiCat, destCatAddDir, imgpre))
                                    
                    tgrid = 4
                    tsize = 500
                    tzoom = 2
                    timg = getThumbnail(self.tmpDir, self.simTmpResi, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
                    timg = scipy.ndimage.zoom(timg, tzoom, order=0)
                    preViewPath = "%s/%s_resi.jpg"%(self.preViewSimResiDir, imgpre)
                    Image.fromarray(timg).save(preViewPath)
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("sim: %s use %d seconds"%(imgName, runTime))
                
                #break
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
    
    def imgCombine(self, srcFitDir, destFitDir, cmbNum = 5):
    
        try:
            destFitDir = "%s/%03d"%(destFitDir, cmbNum)
            if not os.path.exists(destFitDir):
                os.system("mkdir -p %s"%(destFitDir))
                
            tfiles0 = os.listdir(srcFitDir)
            tfiles0.sort()
            
            tfiles = []
            for tfile in tfiles0:
                if tfile.find('mon_objt_190116')>0:
                    tfiles.append(tfile)
            
            #tnum = len(tfiles)-1
            tnum = len(tfiles)
            totalCmb = math.ceil(tnum*1.0/cmbNum)
            print("total cmb %d"%(totalCmb))
            for i in range(totalCmb):
                
                starttime = datetime.now()
                self.log.info("\n\n**********\nsimulate %d: %s"%(i, tfiles[i*cmbNum+1]))
                
                imgs = []
                for j in range(1,cmbNum+1):
                    tIdx = i*cmbNum+j
                    if tIdx > tnum-1:
                        break
                    tname = tfiles[tIdx]
                    self.log.info("read %d, %s"%(tIdx, tname))
                    tdata1 = fits.getdata("%s/%s"%(srcFitDir, tname)) #first image is template
                    imgs.append(tdata1)
                imgArray = np.array(imgs)
                #imgCmb = np.median(imgArray,axis=0).astype(np.int32)
                imgCmb = np.mean(imgArray,axis=0).astype(np.int32)
                
                outImgName = "%s_cmb%03d"%(tfiles[i*cmbNum+1].split('.')[0], imgArray.shape[0])
                fits.writeto("%s/%s.fit"%(destFitDir, outImgName), imgCmb)
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("sim: %s use %d seconds"%(tfiles[i*cmbNum+1], runTime))
                #break
                
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
            
            
    def superCombine(self, srcFitDir, destFitDir, cmbNum = 5, regions=[2,2]):
    
        try:
            destFitDir = "%s/%03d"%(destFitDir, cmbNum)
            if not os.path.exists(destFitDir):
                os.system("mkdir -p %s"%(destFitDir))
                
            tfiles0 = os.listdir(srcFitDir)
            tfiles0.sort()
            
            tfiles = []
            for tfile in tfiles0:
                if tfile.find('mon_objt_190116')>0:
                    tfiles.append(tfile)
            
            #tnum = len(tfiles)-1
            tnum = len(tfiles)
            totalCmb = math.floor(tnum*1.0/cmbNum)
            print("total cmb %d"%(totalCmb))
            for i in range(totalCmb):
                
                starttime = datetime.now()
                self.log.info("\n\n**********\nsimulate %d: %s"%(i, tfiles[i*cmbNum+1]))
                
                tCmbImg = np.array([])
                regWid = 0
                regHei = 0
                for ty in range(regions[0]):
                    for tx in range(regions[1]):
                        imgs = []
                        for j in range(1,cmbNum+1):
                            tIdx = i*cmbNum+j
                            #tIdx = tnum - (i*cmbNum+j)
                            if tIdx > tnum-1 or tIdx <0:
                                break
                            tname = tfiles[tIdx]
                            self.log.info("read %d, %s"%(tIdx, tname))
                            tdata1 = fits.getdata("%s/%s"%(srcFitDir, tname)) #first image is template
                            if tCmbImg.shape[0]==0:
                                tCmbImg=tdata1.copy()
                                regWid = int(tCmbImg.shape[1]/2)
                                regHei = int(tCmbImg.shape[0]/2)
                            imgs.append(tdata1[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid])
                        imgArray = np.array(imgs)
                        tCmbImg[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid] = np.median(imgArray,axis=0)
                
                tCmbImg = tCmbImg.astype(np.int32)
                outImgName = "%s_cmb%03d"%(tfiles[i*cmbNum+1].split('.')[0], imgArray.shape[0])
                fits.writeto("%s/%s.fit"%(destFitDir, outImgName), tCmbImg)
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("sim: %s use %d seconds"%(tfiles[i*cmbNum+1], runTime))
                #break
                
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
            
    def batchCombine(self, srcFitDir, destFitDir):
        
        try:            
            tCatAdd = "/data3/simulationTest/20190325/simCatAdd/G031_mon_objt_190116T20321726.cat"
            tdata = np.loadtxt(tCatAdd)
            ds9RegionName = "%s/simAdd_ds9.reg"%(destFitDir)
            with open(ds9RegionName, 'w') as fp1:
                for tobj in tdata:
                   fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 10\"\n"%
                   (tobj[0], tobj[1], 4.0, tobj[2]))
                        
            #self.imgCombine(srcFitDir, destFitDir, cmbNum = 5)
            #self.imgCombine(srcFitDir, destFitDir, cmbNum = 25)
            #self.imgCombine(srcFitDir, destFitDir, cmbNum = 125)
            #self.imgCombine(srcFitDir, destFitDir, cmbNum = 200)
            self.superCombine(srcFitDir, destFitDir, cmbNum = 400)
            '''  
            srcFitDir2 = "%s/025"%(destFitDir)
            self.imgCombine(srcFitDir2, destFitDir, cmbNum = 400)
            '''
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
            
              
    def simCombineDiff(self, srcDir, destDir):
                
        try:
            if not os.path.exists(destDir):
                os.system("mkdir -p %s"%(destDir))
                
            tfiles0 = os.listdir(srcDir)
            tfiles0.sort()
            
            tempName = ''
            tfiles = []
            for tfile in tfiles0:
                if tfile.find('template')>-1:
                    tempName= tfile
                else:
                    tfiles.append(tfile)
            
            os.system("rm -rf %s/*"%(self.templateDir))
            os.system("cp %s/%s %s/%s"%(srcDir, tempName, self.templateDir, self.templateImg))
            
            for i, imgName in enumerate(tfiles):
                
                starttime = datetime.now()
                self.log.info("diff %d: %s"%(i, imgName))
                
                os.system("rm -rf %s/*"%(self.tmpDir))
                imgpre= imgName.split(".")[0]
                tobjFitsFullPath = "%s/%s.fit"%(srcDir, imgpre)
                if not os.path.exists(tobjFitsFullPath):
                    self.log.error("%s.fit not exist, stop"%(imgpre))
                    break
                
                if os.path.exists("%s/%s.fit"%(destDir, imgpre)):
                    self.log.info("%s.fit already diffed, skip"%(imgpre))
                    continue
                
                os.system("cp %s/%s.fit %s/%s"%(srcDir, imgpre, self.tmpDir, self.objectImg))
                os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
                
                self.objTmpResi, runSuccess = self.tools.runHotpants(self.objectImg, self.templateImg, self.tmpDir)
                if not runSuccess:
                    self.log.info("%s.fit diff error..."%(imgpre))
                    continue
        
                os.system("cp %s/%s %s/%s.fit"%(self.tmpDir, self.objTmpResi, destDir, imgpre))
                
                '''
                odata = fits.getdata("%s/%s"%(self.tmpDir, self.objectImg))
                tdata = fits.getdata("%s/%s"%(self.tmpDir, self.templateImg))
                ddata = odata - tdata
                ddata = ddata.astype(np.int32)
                fits.writeto("%s/%s_dd.fit"%(destDir, imgpre), ddata)
                      '''
                      
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("diff: %s use %d seconds"%(imgName, runTime))
                
                #break
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
            
    def batchSimCombineDiff(self, srcDir, destDir):
        
        try:
            
            tfiles0 = os.listdir(srcDir)
            tfiles0.sort()
            
            tpaths = []
            for tfile in tfiles0:
                if len(tfile)==3:
                    tpaths.append(tfile)
            for tpath in tpaths:
                if tpath == '400':
                    sDirs = "%s/%s"%(srcDir, tpath)
                    dDirs = "%s/%s"%(destDir, tpath)
                    self.simCombineDiff(sDirs, dDirs)
            
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        
    def simSextractor(self, srcFitDir, destFitDir,sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']):
        
        try:
            if not os.path.exists(destFitDir):
                os.system("mkdir -p %s"%(destFitDir))
                
            tfiles0 = os.listdir(srcFitDir)
            tfiles0.sort()
            
            tfiles = []
            for tfile in tfiles0:
                tfiles.append(tfile)
                        
            #os.system("cp /data3/simulationTest/20190325/simCatAdd/G031_mon_objt_190116T20321726.cat %s/%s"%
            #    (self.templateDir, self.templateImgCat))
                
            tdata1 = np.loadtxt("/data3/simulationTest/20190325/simCatAdd/G031_mon_objt_190116T20321726.cat")
            
            tdata2 = tdata1[:2000]
            tdata3 = tdata1[2000:]
            
            tempName1 = "ti_star.cat"
            tempName2 = "ti_galaxy.cat"
            np.savetxt("%s/%s"%(self.templateDir, tempName1), tdata2, fmt='%.5f',delimiter=' ')
            np.savetxt("%s/%s"%(self.templateDir, tempName2), tdata3, fmt='%.5f',delimiter=' ')
        
        
            fpar='sex_diff.par'
            
            for i, imgName in enumerate(tfiles):
                
                starttime = datetime.now()
                self.log.info("\n\n**********\nsextractor %d: %s"%(i, imgName))
                
                os.system("rm -rf %s/*"%(self.tmpDir))
                imgpre= imgName.split(".")[0]
                os.system("cp %s/%s.fit %s/%s"%(srcFitDir, imgpre, self.tmpDir, self.objectImg))
                os.system("cp %s/%s %s/%s"%(self.templateDir, tempName1, self.tmpDir, tempName1))
                os.system("cp %s/%s %s/%s"%(self.templateDir, tempName2, self.tmpDir, tempName2))
                
                self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf=sexConf)
                os.system("cp %s/%s %s/%s.cat"%(self.tmpDir, self.objectImgCat, destFitDir, imgpre))
                
                mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, tempName1, self.objectImgCat, 1)
                
                os.system("cp %s/%s %s/%s_starmch.cat"%(self.tmpDir, mchFile, destFitDir, imgpre))
                os.system("cp %s/%s %s/%s_starnmh.cat"%(self.tmpDir, nmhFile, destFitDir, imgpre))
                
                mchReg = getDs9Reg(mchFile, self.tmpDir)
                nmhReg = getDs9Reg(nmhFile, self.tmpDir)
                
                if len(mchReg)>0:
                    os.system("cp %s/%s %s/%s_starmch.reg"%(self.tmpDir, mchReg, destFitDir, imgpre))
                if len(nmhReg)>0:
                    os.system("cp %s/%s %s/%s_starnmh.reg"%(self.tmpDir, nmhReg, destFitDir, imgpre))
                    
                mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, tempName2, self.objectImgCat, 1)
                
                os.system("cp %s/%s %s/%s_galaxymch.cat"%(self.tmpDir, mchFile, destFitDir, imgpre))
                os.system("cp %s/%s %s/%s_galaxynmh.cat"%(self.tmpDir, nmhFile, destFitDir, imgpre))
                
                mchReg = getDs9Reg(mchFile, self.tmpDir)
                nmhReg = getDs9Reg(nmhFile, self.tmpDir)
                
                if len(mchReg)>0:
                    os.system("cp %s/%s %s/%s_galaxymch.reg"%(self.tmpDir, mchReg, destFitDir, imgpre))
                if len(nmhReg)>0:
                    os.system("cp %s/%s %s/%s_galaxynmh.reg"%(self.tmpDir, nmhReg, destFitDir, imgpre))
                
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("sextractor: %s use %d seconds"%(imgName, runTime))
                
                #break
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        
    def batchSimSextractor(self, srcDir, destDir):
        
        try:
            
            tfiles0 = os.listdir(srcDir)
            tfiles0.sort()
            
            tpaths = []
            for tfile in tfiles0:
                if len(tfile)==3:
                    tnum = int(tfile)
                    if tnum>0:
                        tpaths.append(tfile)
            
            sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','1.8','-ANALYSIS_THRESH','1.8']
            for tpath in tpaths:
                sDirs = "%s/%s"%(srcDir, tpath)
                dDirs = "%s/3/%s"%(destDir, tpath)
                self.simSextractor(sDirs, dDirs, sexConf)
            
            sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.9','-ANALYSIS_THRESH','2.9']
            for tpath in tpaths:
                sDirs = "%s/%s"%(srcDir, tpath)
                dDirs = "%s/5/%s"%(destDir, tpath)
                self.simSextractor(sDirs, dDirs, sexConf)
                
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        
def run1():
    
    #toolPath = os.getcwd()
    toolPath = '/home/gwac/img_diff_xy/image_diff'
    tools = AstroTools(toolPath)
    
    dataDest0 = "/data3/simulationTest"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    
    srcPath00='/data2/G003_031_190116/f_20620425'
    dateStr='20190325'
    camName='G031'
    curSkyId='123'
    
    dataDest='%s/%s'%(dataDest0, dateStr)
    
    dCatDir="%s/dcats"%(dataDest)
    simFitsDir="%s/simFits"%(dataDest)
    cmbFitsDir="%s/cmbFits"%(dataDest)
    cmbFitsDir2="%s/cmbFits2"%(dataDest)
    cmbDiffDir="%s/cmbDiff"%(dataDest)
    cmbDiffCatDir="%s/cmbDiffCat"%(dataDest)
    alignFitsDir="%s/alignFits"%(dataDest)
    alignCatsDir="%s/alignCats"%(dataDest)
    resiFitDir="%s/resiFit"%(dataDest)
    resiCatDir="%s/resiCat"%(dataDest)
    preViewDir="%s/preview"%(dataDest)
    preViewSimResiDir="%s/previewSimResi"%(dataDest)
    simCatAddDir="%s/simCatAdd"%(dataDest)
    
    if not os.path.exists(dCatDir):
        os.system("mkdir -p %s"%(dCatDir))
    if not os.path.exists(simFitsDir):
        os.system("mkdir -p %s"%(simFitsDir))
    if not os.path.exists(cmbFitsDir):
        os.system("mkdir -p %s"%(cmbFitsDir))
    if not os.path.exists(cmbFitsDir2):
        os.system("mkdir -p %s"%(cmbFitsDir2))
    if not os.path.exists(alignFitsDir):
        os.system("mkdir -p %s"%(alignFitsDir))
    if not os.path.exists(alignCatsDir):
        os.system("mkdir -p %s"%(alignCatsDir))
    if not os.path.exists(resiFitDir):
        os.system("mkdir -p %s"%(resiFitDir))
    if not os.path.exists(resiCatDir):
        os.system("mkdir -p %s"%(resiCatDir))
    if not os.path.exists(preViewDir):
        os.system("mkdir -p %s"%(preViewDir))
    if not os.path.exists(preViewSimResiDir):
        os.system("mkdir -p %s"%(preViewSimResiDir))
    if not os.path.exists(simCatAddDir):
        os.system("mkdir -p %s"%(simCatAddDir))
    if not os.path.exists(cmbDiffDir):
        os.system("mkdir -p %s"%(cmbDiffDir))
    if not os.path.exists(cmbDiffCatDir):
        os.system("mkdir -p %s"%(cmbDiffCatDir))
            
    tsim = BatchImageSim(srcPath00, dataDest, tools, camName, curSkyId)
    
    tsim.log.info("\n\n***************\nstart run Sextractor..\n")
    #tsim.getCats(srcPath00, dCatDir)
    
    tsim.log.info("\n\n***************\nstart align image..\n")
    tsim.imgAlign()
    
    tsim.log.info("\n\n***************\nstart sim image..\n")
    #tsim.imgSimulate(alignFitsDir, simFitsDir, simCatAddDir)

    tsim.log.info("\n\n***************\nstart diff image..\n")
    tsim.imgDiff(alignFitsDir, resiFitDir)
    
    tsim.log.info("\n\n***************\nstart combine image..\n")
    #tsim.batchCombine(simFitsDir, cmbFitsDir)
    #tsim.batchCombine(alignFitsDir, cmbFitsDir2)
    
    tsim.log.info("\n\n***************\nstart diff simCombine image..\n")
    tsim.batchSimCombineDiff(cmbFitsDir, cmbDiffDir)
    
    tsim.log.info("\n\n***************\nstart diff simCombine image..\n")
    tsim.batchSimSextractor(cmbDiffDir, cmbDiffCatDir)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()
    