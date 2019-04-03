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
from keras.models import load_model

from astrotools import AstroTools
          
def getWindowImg(img, ctrPos, size):
    
    imgSize = img.shape
    hsize = int(size/2)
    tpad = int(size%2)
    ctrX = math.ceil(ctrPos[0])
    ctrY = math.ceil(ctrPos[1])
    
    minx = int(ctrX - hsize)
    maxx = int(ctrX + hsize + tpad)
    miny = int(ctrY - hsize)
    maxy = int(ctrY + hsize + tpad)
    
    widImg = []
    if minx>0 and miny>0 and maxx<imgSize[1] and maxy<imgSize[0]:
        widImg=img[miny:maxy,minx:maxx]
        
    return widImg

def getWindowImgs(objPath, tmpPath, resiPath, datalist, size):
    
    objData = fits.getdata(objPath)
    tmpData = fits.getdata(tmpPath)
    resiData = fits.getdata(resiPath)
    
    subImgs = []
    parms = []
    for td in datalist:
        try:
            objWid = getWindowImg(objData, (td[0], td[1]), size)
            tmpWid = getWindowImg(tmpData, (td[0], td[1]), size)
            resiWid = getWindowImg(resiData, (td[0], td[1]), size)
            
            if len(objWid)>0 and len(tmpWid)>0 and len(resiWid)>0:
                subImgs.append([objWid, tmpWid, resiWid])
                parms.append(td)
                
        except Exception as e:
            tstr = traceback.format_exc()
            print(tstr)
            
    return np.array(subImgs), np.array(parms)
  
def imgTransform(data1, data2, data3, transMethod='none'):
    
    data1[data1<0] = 0
    data2[data2<0] = 0
    data3[data3<0] = 0
    tmax1 = np.max(data1)
    tmax2 = np.max(data2)
    tmax3 = np.max(data3)
    tmax = np.max([tmax1, tmax2,tmax3])

    tminMaxValue = 50
    if transMethod == 'eachMax':
        if tmax1>tminMaxValue and tmax2>tminMaxValue and tmax3>tminMaxValue:
            data1 = data1*255.0/tmax1
            data2 = data2*255.0/tmax2
            data3 = data3*255.0/tmax3
        elif tmax1>tminMaxValue and tmax2<=tminMaxValue and tmax3>tminMaxValue:
            data1 = data1*255.0/tmax1
            data2 = data2
            data3 = data3*255.0/tmax3
        else:
            data1, data2, data3 = np.array([]), np.array([]), np.array([])
    elif transMethod == 'unionMax':
        if tmax<tminMaxValue:
            data1, data2, data3 = np.array([]), np.array([]), np.array([])
        else:
            data1 = data1*255.0/tmax
            data2 = data2*255.0/tmax
            data3 = data3*255.0/tmax
    
    if transMethod == 'eachMax' or transMethod == 'unionMax' or transMethod == 'zscale':
        data1[data1>255] = 255
        data2[data2>255] = 255
        data3[data3>255] = 255
        
        data1 = data1.astype(np.uint8)
        data2 = data2.astype(np.uint8)
        data3 = data3.astype(np.uint8)
    elif transMethod == 'none': #preMethod4
        data1[data1>65535] = 65535
        data2[data2>65535] = 65535
        data3[data3>65535] = 65535
        data1 = data1.astype(np.uint16)
        data2 = data2.astype(np.uint16)
        data3 = data3.astype(np.uint16)
    
    return data1, data2, data3
    
def getImgStamp(imgArray, size=12, padding = 1, transMethod='none'):
    
    rst = np.array([])
    if len(imgArray.shape)==4 and imgArray.shape[0]>0:
        
        imgSize = imgArray[0][0][0].shape[0]
        ctrIdx = math.ceil(imgSize/2.0) - 1
        halfWid = math.floor(size/2.0)
        minIdx = ctrIdx - halfWid - padding
        maxIdx = ctrIdx + halfWid - padding
        
        rstImgs = []
        for timgs in imgArray:
            img1 = timgs[0][minIdx:maxIdx,minIdx:maxIdx]
            img2 = timgs[1][minIdx:maxIdx,minIdx:maxIdx]
            img3 = timgs[2][minIdx:maxIdx,minIdx:maxIdx]
            
            img1, img2, img3 = imgTransform(img1, img2, img3, transMethod)
            if img1.shape[0]>0 and img2.shape[0]>0 and img3.shape[0]>0:
                rstImgs.append([img1,img2,img3])
        rst = np.array(rstImgs)
    return rst

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

        toolsRoot='/home/gwac/img_diff_xy/image_diff'
        self.modelName='model_RealFOT_64_100_fot10w_20190122_dropout.h5'
        self.modelName2='model_128_5_RealFOT_8_190111.h5'
        self.modelPath="%s/tools/mlmodel/%s"%(toolsRoot,self.modelName)
        self.modelPath2="%s/tools/mlmodel/%s"%(toolsRoot,self.modelName2)
        
        self.imgSize = 64
        self.imgSize2 = 8
        self.pbb_threshold = 0.5
        self.model = load_model(self.modelPath)
        self.model2 = load_model(self.modelPath2)
        
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
        
        
    def recognition(self, fname, catPath, objDir, diffDir, dpath, cmbNum):
        
        try:
            if not os.path.exists(dpath):
                os.system("mkdir -p %s"%(dpath))
            
            preName = fname[:29]
            objPath = '%s/%s_cmb%s.fit'%(objDir, preName, cmbNum)
            tmpPath = '%s/template.fit'%(objDir)
            resiPath = '%s/%s_cmb%s.fit'%(diffDir, preName, cmbNum)
            
            catPath = '%s/%s'%(catPath, fname)
            tdata = np.loadtxt(catPath)
            size = 68
            tSubImgs, tParms = getWindowImgs(objPath, tmpPath, resiPath, tdata, size)
        
            if tSubImgs.shape[0]>0:
                timgs = getImgStamp(tSubImgs, size=self.imgSize, padding = 1, transMethod='none')
                preY = self.model.predict(timgs, batch_size=128)
                
                timgs2 = getImgStamp(tSubImgs, size=self.imgSize2, padding = 1, transMethod='none')
                preY2 = self.model2.predict(timgs2, batch_size=128)
                
                predProbs = preY[:, 1]
                predProbs2 = preY2[:, 1]
                trueOT = (predProbs>self.pbb_threshold) & (predProbs2>self.pbb_threshold)
                falseOT = ~((predProbs>self.pbb_threshold) & (predProbs2>self.pbb_threshold))
                totParms = tParms[trueOT]
                fotParms = tParms[falseOT]
                
                imgpre= fname.split(".")[0]
                np.savetxt("%s/%s_tot.cat"%(dpath, imgpre), totParms, fmt='%.5f',delimiter=' ')
                np.savetxt("%s/%s_fot.cat"%(dpath, imgpre), fotParms, fmt='%.5f',delimiter=' ')
                
                if totParms.shape[0]>0:
                    os.system("rm -rf %s/*"%(self.tmpDir))
                    tempName1 = "ti_star.cat"
                    os.system("cp %s/%s_tot.cat %s/%s"%(dpath, imgpre, self.tmpDir, self.objectImgCat))
                    os.system("cp %s/%s %s/%s"%(self.templateDir, tempName1, self.tmpDir, tempName1))
                    
                    mchFile, nmhFile, mchPair = self.tools.runCrossMatch(self.tmpDir, tempName1, self.objectImgCat, 1)
                    
                    os.system("cp %s/%s %s/%s_starmch.cat"%(self.tmpDir, mchFile, dpath, imgpre))
                    os.system("cp %s/%s %s/%s_starnmh.cat"%(self.tmpDir, nmhFile, dpath, imgpre))
                    
                    tdata2 = np.loadtxt("%s/%s"%(self.tmpDir, mchFile))
                    tdata3 = np.loadtxt("%s/%s"%(self.tmpDir, nmhFile))
                    self.log.info("resiOT %d, recognize True %d, match %d, noMatch %d"%
                          (tdata.shape[0], totParms.shape[0], tdata2.shape[0], tdata3.shape[0] ))
                else:
                    self.log.info("resiOT %d, recognize True %d"%
                          (tdata.shape[0], totParms.shape[0]))
                
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
        
    def batchRecognition(self, objDir, diffDir, diffCatDir, otRcgDir):
        
        tdata1 = np.loadtxt("/data3/simulationTest/20190325/simCatAdd/G031_mon_objt_190116T20321726.cat")
        tdata2 = tdata1[:2000]
        tempName1 = "ti_star.cat"
        np.savetxt("%s/%s"%(self.templateDir, tempName1), tdata2, fmt='%.5f',delimiter=' ')
            
        try:
            
            s2ns = os.listdir(diffCatDir)
            for s2n in s2ns:
                spath1 = '%s/%s'%(diffCatDir, s2n)
                dpath1 = '%s/%s'%(otRcgDir, s2n)
                if not os.path.exists(dpath1):
                    os.system("mkdir -p %s"%(dpath1))
                
                cmbNums = os.listdir(spath1)
                for cmbNum in cmbNums:
                    
                    diffDir2 = '%s/%s'%(diffDir, cmbNum)
                    objDir2 = '%s/%s'%(objDir, cmbNum)
                    
                    spath2 = '%s/%s'%(spath1, cmbNum)
                    dpath2 = '%s/%s'%(dpath1, cmbNum)
                    if not os.path.exists(dpath2):
                        os.system("mkdir -p %s"%(dpath2))
                    
                    self.log.info(spath2)
                    cats = os.listdir(spath2)
                    for tcat in cats:
                        if len(tcat)==len('G031_mon_objt_190116T20334726_cmb005.cat'):
                            self.recognition(tcat, spath2, objDir2, diffDir2, dpath2, cmbNum)
                    
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
    
    otRcgDir="%s/otrcg"%(dataDest)
    diffCatDir="%s/cmbDiffCat"%(dataDest)
    diffDir="%s/cmbDiff"%(dataDest)
    objDir="%s/cmbFits"%(dataDest)
    
    if not os.path.exists(otRcgDir):
        os.system("mkdir -p %s"%(otRcgDir))
            
    tsim = BatchImageSim(srcPath00, dataDest, tools, camName, curSkyId)
        
    tsim.log.info("\n\n***************\nstart recognition diff OTs..\n")
    tsim.batchRecognition(objDir, diffDir, diffCatDir, otRcgDir)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()
    