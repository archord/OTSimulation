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

from gwac_util import getThumbnail, genPSFView, getWindowImgs, getLastLine, selectTempOTs, filtOTs, filtByEllipticity
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

                if i%50!=1 and i<400:                
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
            
    def imgSimulate(self, srcFitDir, destFitDir, destCatAddDir):
        
        try:
            tfiles0 = os.listdir(srcFitDir)
            tfiles0.sort()
            
            tfiles = []
            for tfile in tfiles0:
                if tfile.find('mon_objt_190116')>0:
                    tfiles.append(tfile[:33])
            
            os.system("rm -rf %s/*"%(self.templateDir))
            tmpImgName = tfiles[0]
            os.system("cp %s/%s %s/%s"%(srcFitDir, tmpImgName, self.templateDir, self.templateImg))
            sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']
            fpar='sex_diff.par'
            self.tmpImgCat = self.tools.runSextractor(self.templateImg, self.templateDir, self.templateDir, fpar, sexConf=sexConf)
            
            imgSimClass = ImageSimulation(self.tmpDir)
            for i, imgName in enumerate(tfiles[1:]):
                
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
                os.system("cp %s/%s %s/%s"%(self.templateDir, self.tmpImgCat, self.tmpDir, self.tmpImgCat))
                os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
                
                #sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
                sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3']
                self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf=sexConf)
                mchFile16, nmhFile16 = self.tools.runSelfMatch(self.tmpDir, self.objectImgCat, 16)
                self.osn16 = nmhFile16
                
                osn16s = selectTempOTs(self.osn16, self.tmpDir)
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
                    
                simFile, simPosFile, simDeltaXYA, tmpOtImgs = imgSimClass.simulateImage1(osn32f, self.objectImg, 
                                                                                         osn16sf, self.objectImg, posmagFile=tposmagFile)
                self.objectImgSim = simFile
                self.objectImgSimCatAdd = simPosFile
                                
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
                
                #destFitDir, destCatAddDir
                os.system("cp %s/%s %s/%s.fit"%(self.tmpDir, self.objectImgSim, destFitDir, imgpre))
                os.system("cp %s/%s %s/%s_simResi.fit"%(self.tmpDir, self.simTmpResi, destFitDir, imgpre))
                os.system("cp %s/%s %s/%s.cat"%(self.tmpDir, self.objectImgSimCatAdd, destCatAddDir, imgpre))
                os.system("cp %s/%s %s/%s_simResi.cat"%(self.tmpDir, self.simTmpResiCat, destCatAddDir, imgpre))
                
                if i==0 or (not os.path.exists("%s/%s"%(self.templateDir,posmagFile))):
                    os.system("cp %s/%s %s/%s"%(self.tmpDir, self.objectImgSimCatAdd, self.templateDir, posmagFile))
                
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
            
def run1():
    
    #toolPath = os.getcwd()
    toolPath = '/home/gwac/img_diff_xy/image_diff'
    tools = AstroTools(toolPath)
    
    dataDest0 = "/data3/simulationTest"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    
    srcPath00='/data2/G003_031_190116/f_20620425'
    dateStr='20190324'
    camName='G031'
    curSkyId='123'
    
    dataDest='%s/%s'%(dataDest0, dateStr)
    
    dCatDir="%s/dcats"%(dataDest)
    simFitsDir="%s/simFits"%(dataDest)
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
            
    tsim = BatchImageSim(srcPath00, dataDest, tools, camName, curSkyId)
    
    tsim.log.info("\n\n***************\nstart run Sextractor..\n")
    tsim.getCats(srcPath00, dCatDir)
    
    tsim.log.info("\n\n***************\nstart align image..\n")
    tsim.imgAlign()
    
    tsim.log.info("\n\n***************\nstart sim image..\n")
    tsim.imgSimulate(alignFitsDir, simFitsDir, simCatAddDir)

    tsim.log.info("\n\n***************\nstart diff image..\n")
    tsim.imgDiff(alignFitsDir, resiFitDir)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()
    