# -*- coding: utf-8 -*-
import numpy as np
import os
from datetime import datetime
import traceback
#import psycopg2
#import cv2
from astropy.wcs import WCS
from astrotools import AstroTools
from astropy.io import fits
import math

            
class BatchImageDiff(object):
    def __init__(self, dataRoot, dataDest, tools): 
        
        self.ffNumber = 0
        self.toolPath = os.getcwd()
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim"
        self.tmpUpload="/dev/shm/gwacupload"
        self.tmpDir="%s/tmp"%(self.tmpRoot)
        self.tmpCat="%s/cat"%(self.tmpRoot)
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        self.modelPath="%s/tools/mlmodel"%(self.toolPath)
        
        #self.dataRoot = "/data/gwac_data"
        self.srcDir0 = "%s"%(dataRoot)
        self.srcDir = "%s"%(dataRoot)
        
        self.catDir="%s/cat"%(dataDest)
        self.wcsDir="%s/wcs"%(dataDest)
        self.remapDir="%s/remap"%(dataDest)
            
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
        self.maxFalseNum = 5
        
        self.tools = tools
        self.log = tools.log
        #self.modelName='model_128_5_RealFOT_8_190111.h5'
        #self.modelName='model_RealFOT_64_100_fot10w_20190122_dropout.h5'
        self.modelName='model_80w_20190403_branch3_train12_79.h5'
        
        self.initReg(0)
                
        if not os.path.exists(self.wcsDir):
            os.system("mkdir -p %s"%(self.wcsDir))
        if not os.path.exists(self.catDir):
            os.system("mkdir -p %s"%(self.catDir))

    
    def initReg(self, idx):
        
        if idx<=0:
            idx =0
            os.system("rm -rf %s/*"%(self.tmpRoot))
            os.system("rm -rf %s/*"%(self.tmpUpload))
        
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
    
    def getCat(self, srcDir, imgName):
        
        starttime = datetime.now()
        
        if os.path.exists(self.tmpDir):
            os.system("rm -rf %s/*"%(self.tmpDir))
        else:
            os.system("mkdir -p %s"%(self.tmpDir))
        
        imgpre= imgName.split(".")[0]
        oImgf = "%s/%s.fit"%(srcDir,imgpre)
        oImgfz = "%s/%s.fit.fz"%(srcDir,imgpre)
        if os.path.exists(oImgf):
            os.system("cp %s/%s.fit %s/%s"%(srcDir, imgpre, self.tmpDir, self.objectImg))
        elif os.path.exists(oImgfz):
            os.system("cp %s/%s.fit.fz %s/%s.fz"%(srcDir, imgpre, self.tmpDir, self.objectImg))
            os.system("%s %s/%s.fz"%(self.funpackProgram, self.tmpDir, self.objectImg))
        else:
            self.log.warning("%s not exist"%(oImgf))
            return False
                
        fieldId, cra,cdec = self.tools.removeHeaderAndOverScan(self.tmpDir,self.objectImg)

        sexConf=['-DETECT_MINAREA','10','-DETECT_THRESH','5','-ANALYSIS_THRESH','5']
        fpar='sex_diff.par'
        self.objectImgCat = self.tools.runSextractor(self.objectImg, self.tmpDir, self.tmpDir, fpar, sexConf)
        os.system("cp %s/%s %s/%s.cat"%(self.tmpDir, self.objectImgCat, self.catDir, imgpre))
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        #self.log.info("********** get cat %s use %d seconds"%(imgName, runTime))
        print("********** get cat %s use %d seconds"%(imgName, runTime))

         
def run1():
    
    storePath = '/home/xy/work/imgDiffTest2'
    #toolPath = os.getcwd()
    toolPath = '/home/xy/Downloads/myresource/deep_data2/image_diff'
    tools = AstroTools(toolPath)
    
    dataDest0 = "/home/xy/work/gwac_diff_xy/data"
    logDest0 = "/home/xy/work/gwac_diff_xy/log"
    
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
    if not os.path.exists(logDest0):
        os.system("mkdir -p %s"%(logDest0))
    
    dateStr='190829'
    
    tdates = os.listdir(storePath)
    
    print("total has %d date&ccd"%(len(tdates)))
    
    for i, tdate in enumerate(tdates):

        dstDir='%s/%s/%s'%(dataDest0, dateStr, tdate)
        tdiff = BatchImageDiff(storePath, dstDir, tools)
        tpath1 = '%s/%s'%(storePath,tdate)
        timgs = os.listdir(tpath1)
        timgs.sort()
        print("total has %d images"%(len(timgs)))
        
        for j, tname in enumerate(timgs):
                
            try:
                tpath = "%s/%s"%(tpath1, tname)
                if not os.path.exists(tpath):
                    print("%s not exist"%(tpath))
                    continue
                
                print("process %d %s"%(j, tname))
                tdiff.getCat(tpath1, tname)
                
            except Exception as e:
                print(str(e))
                tstr = traceback.format_exc()
                print(tstr)
        
            
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    run1()