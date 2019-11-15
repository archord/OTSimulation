# -*- coding: utf-8 -*-

import time
import traceback
from datetime import datetime
import os
import sys
import numpy as np

from GWACDiff import GWACDiff
from QueryData import QueryData
from astrotools import AstroTools
from gwac_util import getLastLine

        
class BatchImageDiff(object):
    
    def __init__(self):
        
        self.initData()
        
        self.crossTaskParms = {'mergedR': 0.0167, 
                  'mergedMag': 20, 
                  'cvsR': 0.0167,
                  'cvsMag': 20, 
                  'rc3R': 0.03333, 
                  'rc3MinMag': -20, 
                  'rc3MaxMag': 20, 
                  'minorPlanetR': 0.05, 
                  'minorPlanetMag': 16, 
                  'ot2HisR': 0.01, 
                  'ot2HisMag': 20, 
                  'usnoR1': 0.016667, 
                  'usnoMag1': 15.5, 
                  'usnoR2': 0.041667, 
                  'usnoMag2': 8}
    
    def initData(self):
        self.catList = []
        self.alignTmplMap = {}
        self.alignList = []
        self.cmbImgList = []
        self.cmbCatList = []
        self.diffTmplMap = {}
        self.diffImgList = []

        self.alignTmplIdx = -1
        self.alignIdx = -1
        self.cmbIdx = -1
        self.cmbCatIdx = -1
        self.diffTmplIdx = -1
        self.diffIdx = -1
        self.recgIdx = -1
        
        self.catRunning = 0
        self.alignTmplRunning = 0
        self.alignRunning = 0
        self.cmbRunning = 0
        self.cmbCatRunning = 0
        self.diffTmplRunning = 0
        self.diffRunning = 0
        self.recgRunning = 0
        
        self.skyName0 = ""
        self.curFFId = 0
        self.loopNum = 0
                
    def srcExtract(self, tpath, camName, catList, imgDiff, logDestDir, runName):
        
        self.catRunning = 1
                    
        ffId = 0
        tfiles = os.listdir(tpath)
        tfiles.sort()
        print("srcExtract: total read %d files"%(len(tfiles)))
        
        for i, tfile in enumerate(tfiles):
            try:
                if tfile[-3:]!='fit':
                    continue
                curSkyId = 0
                timgName = tfile #G021_tom_objt_190109T13531492.fit
                srcDir= "%s/%s"%(tpath, timgName) #/data3/G002_021_190109 /home/xy/work/imgDiffTest2/fits/190128_G004_044
                print(srcDir)
    
                tpathfz = "%s.fz"%(srcDir)
                if os.path.exists(srcDir) or os.path.exists(tpathfz):
                    starttime = datetime.now()
                    isSuccess, skyName, starNum, fwhmMean, bgMean = imgDiff.getCat(tpath, timgName, imgDiff.catDir)
                    if isSuccess: #we can add more filter condition, to remove bad images
                        catList.append([isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, tpath])
                    endtime = datetime.now()
                    runTime = (endtime - starttime).seconds
                    imgDiff.log.info("srcExtractLocalDir, totalTime %d seconds, sky:%d, %s"%(runTime, curSkyId, timgName))
                else:
                    imgDiff.log.error("getCat: %s not exist"%(tpath))
                    
                if i>9:
                    break
    
            except Exception as e:
                tstr = traceback.format_exc()
                imgDiff.log.error(tstr)
    
        self.catRunning = 0
        
    def getAlignTemplate(self, camName, catList, tmplMap, imgDiff):
        
        self.alignTmplRunning = 1
        catNum = len(catList)
        print("getAlignTemplate: array has %d images, idx=%d"%(catNum, self.alignTmplIdx))
        
        for i in range(0, catNum):
            try:
                tcatParm = catList[i]
                skyId = tcatParm[7]
                imgPath = tcatParm[8]
                skyName = tcatParm[4]
                imgName = tcatParm[2]
                tmplMap[skyName] = ['1', [(imgName,)],2]
                print("template is:")
                print(tmplMap[skyName])
                
                imgpre= imgName.split(".")[0]
                os.system("cp %s/%s.cat %s/%s.cat"%(imgDiff.catDir, imgpre, imgDiff.tmplAlignDir, imgpre))
                os.system("cp %s/%s.fit %s/%s.fit"%(imgPath, imgpre, imgDiff.tmplAlignDir, imgpre))
                
                self.alignTmplIdx = i
                break
    
            except Exception as e:
                tstr = traceback.format_exc()
                imgDiff.log.error(tstr)
        self.alignTmplRunning = 0
        
    def doAlign(self, camName, catList, tmplMap, alignList, imgDiff):
        
        self.alignRunning = 1
        catNum = len(catList)
        print("doAlign: array has %d images, idx=%d"%(catNum, self.alignIdx))
        if catNum>1:
            lastIdx = self.alignIdx
            if catNum-1>lastIdx:
                for i in range(lastIdx+1, catNum):
                    try:
                        tcatParm = catList[i]
                        skyName = tcatParm[4]
                        imgName = tcatParm[2]
                        srcDir = tcatParm[8]
                        #srcDir = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/190101_G004_041_test2_rst2/data/20191107_p1/A_cat'
    
                        if skyName in tmplMap:
                            tmplParms = tmplMap[skyName]
                            tmplImgs = tmplParms[1]
                            if len(tmplImgs)>0:
                                self.alignIdx = i
                                isSuccess = imgDiff.alignImage(srcDir, imgName, tmplParms)
                                if isSuccess:
                                    alignList.append(tcatParm)
                                    print("doAlign %d: %s %s align success"%(i, camName, imgName))
                                else:
                                    print("doAlign %d: %s %s align failure"%(i, camName, imgName))
                            else:
                                print("doAlign %d: %s, wait template"%(i, imgName))
                                break
                        else:
                            print("doAlign %d: %s %s cannot find template"%(i, skyName, imgName))
                            break
            
                    except Exception as e:
                        tstr = traceback.format_exc()
                        imgDiff.log.error(tstr)
            
        self.alignRunning = 0
        
        
    def doDiff(self, camName, cmbImgList, diffTmplMap, imgDiff, diffImgList):
        
        self.diffRunning = 1
        tNum = len(cmbImgList)
        lastIdx = self.diffIdx
        print("doDiff: array has %d images, idx=%d"%(tNum, self.diffIdx))
        
        if tNum-1>lastIdx:
            for i in range(lastIdx+1, tNum):
                try:
                    tcatParm = cmbImgList[i]
                    skyName = tcatParm[4]
                    imgName = tcatParm[2]
                    #print("start doDiff %s"%(imgName))
    
                    if skyName in diffTmplMap:
                        self.diffIdx = i
                        tmplParms = diffTmplMap[skyName]
                        status = tmplParms[0]
                        if status=='2' or status=='1':
                            print("doDiff %d: %s, sky=%s"%(i, imgName, skyName))
                            isSuccess = imgDiff.diffImage(imgName, tmplParms)
                            if isSuccess:
                                print("doDiff %d: %s %s diff success"%(i, camName, imgName))
                                diffImgList.append(tcatParm)
                        else:
                            print("doDiff: wait template")
                            break
                    else:
                        print("doDiff %d: %s %s cannot find template"%(i, skyName, imgName))
                        break
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
            
        self.diffRunning = 0
            
    
    def mainControl(self, camName, runName = 'p1', destDir='/data/gwac_diff_xy', toolPath='/home/gwac/img_diff_xy/image_diff'):
        
        tools = AstroTools(toolPath)
        logDest0 = "%s/log"%(destDir)
        if not os.path.exists(logDest0):
            os.system("mkdir -p %s"%(logDest0))
            
        dateStr = datetime.strftime(datetime.utcnow(), "%Y%m%d")
        dataDest0 = "%s/data/%s_%s"%(destDir, dateStr, runName)
        if not os.path.exists(dataDest0):
            os.system("mkdir -p %s"%(dataDest0))
        imgDiff = GWACDiff(camName, dataDest0, tools)
        tStr = "%s: start combine diff..."%(camName)
        imgDiff.log.info(tStr)
        
        dataPath = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/cmb'
        
        try:
            self.srcExtract(dataPath, camName, self.catList, imgDiff, logDest0, runName)
            self.getAlignTemplate(camName, self.catList, self.alignTmplMap, imgDiff)
            self.doAlign(camName, self.catList, self.alignTmplMap, self.alignList, imgDiff)
            #self.doCombine(camName, self.alignList, self.alignTmplMap, imgDiff, self.cmbImgList, self.crossTaskParms, runName, 5)
            #self.srcExtractCombine(camName, self.alignList, self.cmbCatList, imgDiff)
            self.doDiff(camName, self.alignList, self.alignTmplMap, imgDiff, self.diffImgList)
            #self.doRecognitionAndUpload(camName, self.diffImgList, self.diffTmplMap, imgDiff, runName)

        except Exception as e:
            tstr = traceback.format_exc()
            print("Scheduling main error....")
            print(tstr)
            time.sleep(10)
        
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    camName = 'G021'
    runName = 'p1'
    destDir = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/cmb_rst'
    toolPath = '/home/xy/Downloads/myresource/deep_data2/image_diff'
    bdiff = BatchImageDiff()
    bdiff.mainControl(camName, runName, destDir, toolPath)