# -*- coding: utf-8 -*-
import scipy.ndimage
import numpy as np
import os
import math
import time
import logging
import datetime
from PIL import Image
from gwac_util import getThumbnail, genPSFView
from QueryData import QueryData

from astrotools import AstroTools

class BatchImageDiff(object):
    def __init__(self, dataRoot, dataDest): 
        
        self.verbose = False
                
        self.toolPath = os.getcwd()
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim"
        self.tmpDir="%s/tmp"%(self.tmpRoot)
        self.tmpCat="%s/cat"%(self.tmpRoot)
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        
        #self.dataRoot = "/data/gwac_data"
        self.srcDir0 = "%s"%(dataRoot)
        self.srcDir = "%s"%(dataRoot)
        
        self.resiCatDir="%s/resiCat"%(dataDest)
        self.destDir="%s/subImg"%(dataDest)
        self.preViewDir="%s/preview"%(dataDest)
        self.origPreViewDir="%s/orig_preview"%(dataDest)
        
        os.system("rm -rf %s/*"%(self.tmpRoot))
                
        if not os.path.exists(self.templateDir):
            os.system("mkdir -p %s"%(self.templateDir))
        if not os.path.exists(self.tmpDir):
            os.system("mkdir -p %s"%(self.tmpDir))
        if not os.path.exists(self.tmpCat):
            os.system("mkdir -p %s"%(self.tmpCat))
        if not os.path.exists(self.resiCatDir):
            os.system("mkdir -p %s"%(self.resiCatDir))
        if not os.path.exists(self.destDir):
            os.system("mkdir -p %s"%(self.destDir))
        if not os.path.exists(self.preViewDir):
            os.system("mkdir -p %s"%(self.preViewDir))
        if not os.path.exists(self.origPreViewDir):
            os.system("mkdir -p %s"%(self.origPreViewDir))
            
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
             
        self.selTemplateNum = 20 # 10 3
        self.imglist = []
        self.origTmplImgName = ""
        self.tmplImgIdx = 0
        
        self.log = logging.getLogger() #create logger
        self.log.setLevel(logging.DEBUG) #set level of logger, DEBUG INFO
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s") #set format of logger
        logging.Formatter.converter = time.gmtime #convert time in logger to UCT
        #filehandler = logging.FileHandler("%s/otSim.log"%(self.destDir), 'w+')
        filehandler = logging.FileHandler("%s/otSim.log"%(self.toolPath), 'w+')
        filehandler.setFormatter(formatter) #add format to log file
        self.log.addHandler(filehandler) #link log file to logger
        if self.verbose:
            streamhandler = logging.StreamHandler() #create print to screen logging
            streamhandler.setFormatter(formatter) #add format to screen logging
            self.log.addHandler(streamhandler) #link logger to screen logging
    
        self.tools = AstroTools(self.toolPath, self.log)

    def register(self, imgName, regIdx, imgIdx):
        
        starttime = datetime.datetime.now()
        
        regSuccess = True
        imgpre= imgName.split(".")[0]
        regCatName = "%s.cat"%(imgpre)
        self.origObjectImg = imgName
        os.system("rm -rf %s/*"%(self.tmpDir))
        
        oImgfz = "%s/%s.fz"%(self.srcDir,imgName)
        if not os.path.exists(oImgfz):
            self.log.warning("%s not exist"%(oImgfz))
            return
                
        os.system("cp %s/%s.fz %s/%s.fz"%(self.srcDir, imgName, self.tmpDir, self.objectImg))
        os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, self.objectImg))
        '''
        os.system("cp %s/%s %s/%s"%(self.srcDir, imgName, self.tmpDir, self.objectImg))
        '''
        
        self.tools.removeHeaderAndOverScan(self.tmpDir,self.objectImg)

        sexConf=['-DETECT_MINAREA','7','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf)
        mchFile16, nmhFile16 = self.tools.runSelfMatch(self.tmpDir, self.objectImgCat, 16)
        
        tobjImgCat = nmhFile16
        os.system("cp %s/%s %s/%s"%(self.tmpDir, tobjImgCat, self.tmpCat, regCatName))
        
        xrms=0
        yrms=0
        tImgNum = len(self.imglist)
        if tImgNum ==0:
            self.imglist.append((regCatName, 0, 0, 0, 0, 0, 99))
        else:
            if tImgNum==1:
                xshift0, yshift0 = 0, 0
            else:
                timgN = self.imglist[-1]
                if regIdx==tImgNum-1:
                    xshift0, yshift0 = 0, 0
                elif regIdx==timgN[1]:
                        xshift0 = timgN[2]
                        yshift0 = timgN[3]
                else:
                    xshift0, yshift0 = 0, 0
                    for tIdx in range(regIdx, tImgNum):
                        timg = self.imglist[tIdx]
                        xshift0 = xshift0 + timg[2]
                        yshift0 = yshift0 + timg[3]
                        
            tImgCat = self.imglist[regIdx][0]
            os.system("cp %s/%s %s/%s"%(self.tmpCat, tImgCat, self.tmpDir, self.templateImgCat))
            self.log.info("%d,%s regist to %d,%s"%(tImgNum, imgName, regIdx, tImgCat))
            
            if imgIdx==492:
                xshift0 = 1.10
                yshift0 = 12.80
            
            xshift0Orig = xshift0
            yshift0Orig = yshift0
            tryShifts = [1.0,0.1,0.3,0.5,0.7,0.9,1.1,1.3,1.5,1.7,1.9,-0.1,-0.3,-0.5,-0.7,-0.9,-1.1,-1.3,-1.5,-1.7,-1.9]
            for tsf in tryShifts:
                if math.fabs(xshift0)>0.000001 and math.fabs(yshift0)>0.000001:
                    xshift0 = tsf*xshift0Orig
                    yshift0 = tsf*yshift0Orig
                    tobjImgCatShift = self.tools.catShift(self.tmpDir, tobjImgCat, xshift0, yshift0)
                else:
                    tobjImgCatShift = tobjImgCat
                
                mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, tobjImgCatShift, self.templateImgCat, 10)
                osn16_tsn16_cm = mchFile
                osn16_tsn16_cm_pair = mchPair
                
                tNumMean, tNumMin, tNumRms = self.tools.gridStatistic(self.tmpDir, osn16_tsn16_cm, self.imgSize, gridNum=4)
                fwhmMean, fwhmRms = self.tools.fwhmEvaluate(self.tmpDir, osn16_tsn16_cm)
                
                self.transHG, xshift, yshift, xrms, yrms = self.tools.getMatchPosHmg(self.tmpDir, tobjImgCat, self.templateImgCat, osn16_tsn16_cm_pair)
                self.log.info("astrometry pos transform, xshift0=%.2f, yshift0=%.2f"%(xshift0, yshift0))
                self.log.info("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
                
                if imgIdx>=self.selTemplateNum and xrms<1 and yrms<1:
                    self.newImageName = self.tools.imageAlign(self.tmpDir, self.objectImg, self.transHG)
                
                if xrms<1 and yrms<1:
                    break
                else:
                    if math.fabs(xshift0)>0.000001 and math.fabs(yshift0)>0.000001:
                        self.log.error("astrometry error, shift scale %.1f, retry"%(tsf))
                    else:
                        break
            
            if xrms<1 and yrms<1:
                tinfo = (regCatName, regIdx, xshift, yshift, xrms, yrms, fwhmMean)
                self.imglist.append(tinfo)
                self.log.info(tinfo)
            else:
                self.imglist.append((regCatName, regIdx, 0, 0, 0, 0, 99))
                regSuccess = False
                self.log.error("******%s astrometry failing"%(imgName))
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** regist %s use %d seconds"%(imgName, runTime))
    
        return regSuccess
    
    def makeTemplate(self):
        
        starttime = datetime.datetime.now()
        
        os.system("rm -rf %s/*"%(self.templateDir))
        
        tImgNum = len(self.imglist)
        tparms = []
        for tIdx in range(tImgNum-self.selTemplateNum,tImgNum):
            tparms.append(self.imglist[tIdx])
            
        tparms = np.array(tparms)
        self.log.debug(tparms)
        tfwhms = tparms[:,6].astype(np.float)
        minIdx = np.argmin(tfwhms)
        
        timgCat = tparms[minIdx][0]
        imgpre= timgCat.split(".")[0]
        self.origTmplImgName = "%s.fit"%(imgpre)
        self.tmplImgIdx = tImgNum-self.selTemplateNum + minIdx
        self.log.info("select %dth image %s as template, it has min fwhm %.2f"%(self.tmplImgIdx, self.origTmplImgName, tfwhms[minIdx]))
        
        os.system("rm -rf %s/*"%(self.templateDir))
        
        os.system("cp %s/%s.fz %s/%s.fz"%(self.srcDir, self.origTmplImgName, self.templateDir, self.templateImg))
        os.system("%s %s/%s.fz"%(self.funpackProgram, self.templateDir, self.templateImg))
        '''
        os.system("cp %s/%s %s/%s"%(self.srcDir, self.origTmplImgName, self.templateDir, self.templateImg))
        '''
        self.tools.removeHeaderAndOverScan(self.templateDir, self.templateImg)
        sexConf=['-DETECT_MINAREA','7','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        tmplCat = self.tools.runSextractor(self.templateImg, self.templateDir, self.templateDir, fpar, sexConf, cmdStatus=0)
        
        objName = 'ti.fit'
        bkgName = 'ti_bkg.fit'
        self.badPixCat = self.tools.processBadPix(objName, bkgName, self.templateDir, self.templateDir)
        
        #do astrometry, get wcs    
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** make template %s use %d seconds"%(self.origTmplImgName, runTime))
        
    def diffImage(self):
        
        starttime = datetime.datetime.now()
        
        oImgPre = self.origObjectImg[:self.origObjectImg.index(".")]
        
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.badPixCat, self.tmpDir, self.badPixCat))
        os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImgCat, self.tmpDir, self.templateImgCat))
        
        #self.newImageName = self.tools.imageAlign(self.tmpDir, self.objectImg, self.transHG)
                
        self.objTmpResi = self.tools.runHotpants(self.newImageName, self.templateImg, self.tmpDir)
        '''
        tgrid = 4
        tsize = 500
        tzoom = 1
        timg = getThumbnail(self.tmpDir, self.objTmpResi, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_resi.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        timg = getThumbnail(self.tmpDir, newImageName, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_obj.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        timg = getThumbnail(self.tmpDir, self.templateImg, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
        timg = scipy.ndimage.zoom(timg, tzoom, order=0)
        preViewPath = "%s/%s_tmp.jpg"%(self.origPreViewDir, oImgPre)
        Image.fromarray(timg).save(preViewPath)
        '''
        fpar='sex_diff.par'
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        resiCat = self.tools.runSextractor(self.objTmpResi, self.tmpDir, self.tmpDir, fpar, sexConf)
        
        '''
        self.tools.runSelfMatch(self.tmpDir, resiCat, 1) #debug: get ds9 reg file
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, resiCat))
        self.log.info("resi image star %d"%(tdata.shape[0]))
        '''
        '''
        mchRadius = 10
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, resiCat, self.templateImgCat, mchRadius)
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
        print("resi star not match template %d"%(tdata.shape[0]))
        '''
        mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, resiCat, self.badPixCat, 1) #1 and 5 
        os.system("cp %s/%s %s/%s"%(self.tmpDir, nmhFile, self.resiCatDir, "%s.cat"%(oImgPre)))
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, nmhFile))
        self.log.info("resi star not match template and remove badpix %d"%(tdata.shape[0]))
        
        if tdata.shape[0]<5000:
            size = self.subImgSize
            fSubImgs, fparms = self.tools.getWindowImgs(self.tmpDir, newImageName, self.templateImg, self.objTmpResi, tdata, size)
            
            fotpath = '%s/%s_otimg_fot.npz'%(self.destDir, oImgPre)
            np.savez_compressed(fotpath, fot=fSubImgs, parms=fparms)
                    
            resiImgs = []
            for timg in fSubImgs:
                resiImgs.append(timg[2])
    
            preViewPath = "%s/%s_psf.jpg"%(self.preViewDir, oImgPre)
            #if not os.path.exists(preViewPath):
            psfView = genPSFView(resiImgs)
            Image.fromarray(psfView).save(preViewPath)
        else:
            self.log.error("resi image has too many objects, maybe wrong")
                        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** image diff total use %d seconds"%(runTime))
        
        ''' '''
    def batchSim(self):
        
        query = QueryData()
        filesNum = query.queryFilesNum()
        
        for tnum in filesNum:
            
            if tnum[3]>1000 and tnum[2]%5>0:
                files = query.getFileList(tnum[1], tnum[2], tnum[0])
                total = len(files)
                self.log.info(tnum)
                
                ccd = files[0][1]
                #G004_041
                tpath1 = "G0%s_%s"%(ccd[:2], ccd)
                self.srcDir="%s/%s/%s"%(self.srcDir0,tnum[0], tpath1)
                
                regFalseNum = 0
                self.imglist = []
                for i in range(total):
                    self.log.debug("\n\n************%d"%(i))
                    objectImg = files[i][0]
                    if i<self.selTemplateNum:
                        self.register(objectImg, i-1, i)
                    if i>=self.selTemplateNum:
                        if self.tmplImgIdx==0:
                            self.makeTemplate()
                        if i>=492:
                            regSuccess = self.register(objectImg, self.tmplImgIdx, i)
                            if regSuccess:
                                self.diffImage()
                            else:
                                regFalseNum = regFalseNum +1
                    if regFalseNum>5:
                        self.log.error("more than %d image regist failing, stop")
                        break
                    #if i>5:
                    #    break
                    
            break
        
    def batchSim2(self):
        
        flist = os.listdir(self.srcDir)
        flist.sort()
        
        imgs = []
        for tfilename in flist:
            if tfilename.find("fit")>-1:
                imgs.append(tfilename)
        
        totalImg = len(imgs)
        print("total image %d"%(len(imgs)))
        
        for i in range(totalImg):
            
            objectImg = imgs[i]
            if i<self.selTemplateNum:
                self.register(objectImg, i-1, i)
            if i>=self.selTemplateNum:
                if self.tmplImgIdx==0:
                    self.makeTemplate()
                if i>500 and i%10==1:
                    self.register(objectImg, self.tmplImgIdx, i)
                    self.diffImage()
                if i>502:
                    break
                
            #if i>5:
            #    break
        

def run1():
    
    dataRoot = "/data/gwac_data/gwac_orig_fits"
    dataDest = "/data/gwac_data/gwac_simot/data_1222"
    
    tdiff = BatchImageDiff(dataRoot, dataDest)
    tdiff.batchSim()
    
def run2():
    
    dataRoot = "/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0"
    dataDest = "/home/xy/Downloads/myresource/deep_data2/simot/data_1221"
    
    tdiff = BatchImageDiff(dataRoot, dataDest)
    tdiff.batchSim2()
    
if __name__ == "__main__":
    
    run1()
    #run2()
    