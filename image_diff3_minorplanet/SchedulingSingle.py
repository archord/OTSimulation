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
                
    def srcExtract(self, camName, catList, tmplMap, imgDiff, logDestDir, runName):
        
        self.catRunning = 1
                    
        query = QueryData()
        tfiles = query.getFileList(camName, self.curFFId)
        
        tnum = len(tfiles)
        tstr = "%s, secExtract: get %d images, ffId=%d"%(camName, tnum, tfiles[0][0])
        print(tstr)
        if tnum>0:
            imgDiff.sendMsg(tstr)
            
        for tfile in tfiles:
            
            try:
                curFfId = tfile[0]
                ffNumber = tfile[1]
                curSkyId = tfile[2]
                timgName = tfile[3] #G021_tom_objt_190109T13531492.fit
                tpath = tfile[4] #/data3/G002_021_190109/G021_tom_objt_190109T13531492.fit
                skyName = tfile[5]
                
                if skyName not in tmplMap:
                    print("srcExtract: %s"%(tpath))
                else:
                    tparms = tmplMap[skyName] #['2', [],1]
                    if tparms[0]!='1':
                        print("srcExtract: %s, no history template, skip"%(tpath))
                        continue
                
                srcDir= tpath[:(tpath.find(camName)-1)] #/data3/G002_021_190109
                dateStr = srcDir[srcDir.find('G'):] #G002_021_190109
                logfName0 = '%s/%s_%s.log'%(logDestDir, dateStr, runName)
                
                if self.curFFId==0:
                    if os.path.exists(logfName0) and os.stat(logfName0).st_size > 0:
                        tlastLine = getLastLine(logfName0)
                        if len(tlastLine)>2:
                            self.curFFId=int(tlastLine.strip())
    
                if curFfId>self.curFFId:
                    self.curFFId=curFfId
                    
                    logfile0 = open(logfName0, 'a')
                    logfile0.write("\n\n%d\n"%(self.curFFId))
                    logfile0.close()
                    
                    tpathfz = "%s.fz"%(tpath)
                    if os.path.exists(tpath) or os.path.exists(tpathfz):
                        isSuccess, skyName, starNum, fwhmMean, bgMean = imgDiff.getCat(srcDir, timgName, imgDiff.catDir)
                        if isSuccess: #we can add more filter condition, to remove bad images
                            catList.append([isSuccess, self.curFFId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, srcDir])
                            print("srcExtract %d: %s success."%(len(catList), tpath))
                        else:
                            print("srcExtract %d: %s failure."%(len(catList), tpath))
                    else:
                        print("getCat: %s not exist"%(tpath))
    
            except Exception as e:
                tstr = traceback.format_exc()
                imgDiff.log.error(tstr)
    
        self.catRunning = 0
        
    def getAlignTemplate(self, camName, catList, tmplMap, imgDiff):
        
        self.alignTmplRunning = 1
        catNum = len(catList)
        print("getAlignTemplate: array has %d images, idx=%d"%(catNum, self.alignTmplIdx))
        newTmplSelectNum = 10
        if catNum>=newTmplSelectNum:
            lastIdx = self.alignTmplIdx
            if catNum-1>lastIdx:
                hasCenterCoor = False
                raCenter, decCenter = 0, 0
                for i in range(catNum-1, lastIdx, -1):
                    try:
                        tcatParm = catList[i]
                        tpath = tcatParm[8]
                        skyName = tcatParm[4]
                        imgName = tcatParm[2]
                        
                        if skyName not in tmplMap:
                            runSuccess, raCenter, decCenter = imgDiff.getImgCenter(tpath, imgName)
                            if runSuccess:
                                hasCenterCoor = True
                                break
                        else:
                            break
                    except Exception as e:
                        tstr = traceback.format_exc()
                        imgDiff.log.error(tstr)
                for i in range(lastIdx+1, catNum):
                    try:
                        tcatParm = catList[i]
                        skyId = tcatParm[7]
                        skyName = tcatParm[4]
                        imgName = tcatParm[2]
                        
                        if skyName not in tmplMap:
                            print("getAlignTemplate %d: %s, sky(%s) is new, query align template from database"%(i, imgName, skyName))
                            print("getAlignTemplate: image(ra,dec)=(%f,%f)"%(raCenter, decCenter))
                            if hasCenterCoor:
                                query = QueryData()
                                tmpls = query.getTmplList(camName, skyId, raCenter, decCenter)
                                #tmpls = query.getTmplList(camName, skyId)
                                if len(tmpls)>0:
                                    print("getAlignTemplate %d: %s, sky(%s) is new, query align template from database success, default tmpName is %s"%(i, imgName, skyName, tmpls[0][0]))
                                    print("getAlignTemplate: image(ra,dec)=(%f,%f), tmpl(ra,dec)=(%f,%f)"%(raCenter, decCenter, tmpls[0][5], tmpls[0][6]))
                                    tparms = ['1',tmpls,1] #status, imgList, currentSky image number
                                    imgDiff.getAlignTemplate(tparms, skyName)
                                    tmplMap[skyName]=tparms 
                                else:
                                    print("getAlignTemplate %d: %s, sky(%s) is new, query align template from database failure, consider select from local"%(i, imgName, skyName))
                                    tmplMap[skyName]=['2', [],1] #status, imgList, currentSky image number
                            else:
                                print("getAlignTemplate %d: %s, sky(%s) is new, query align template from database failure, consider select from local"%(i, imgName, skyName))
                                tmplMap[skyName]=['2', [],1] #status, imgList, currentSky image number
                        else:
                            print("getAlignTemplate %d: %s, sky(%s) is new, just need history template, skip local build template"%(i, imgName, skyName))
                        self.alignTmplIdx = i
            
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
    
                        if skyName in tmplMap:
                            tmplParms = tmplMap[skyName]
                            tmplImgs = tmplParms[1]
                            if len(tmplImgs)>0:
                                self.alignIdx = i
                                isSuccess, t2oX, t2oY = imgDiff.alignImage(srcDir, imgName, tmplParms)
                                if isSuccess:
                                    tlist = tcatParm.copy()
                                    tlist.extend([t2oX, t2oY])
                                    alignList.append(tlist)
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
            
        
    def doCombine(self, camName, alignList, tmplMap, imgDiff, cmbImgList, crossTaskParms, runName, cmbNum=5):
        
        self.cmbRunning = 1
        lastIdx = self.cmbIdx
        catNum = len(alignList)
        print("doCombine: array has %d images, idx=%d"%(catNum, self.cmbIdx))
    
        newSky = False
        startIdx = lastIdx+1
        alignStartIdx = startIdx
        if catNum>=startIdx+cmbNum:
            timgs = []
            for i in range(lastIdx+1, catNum):
                try:
                    tcatParm = alignList[i]
                    skyName = tcatParm[4]
                    imgName = tcatParm[2]
                                        
                    if len(timgs)==0 and len(self.skyName0)==0:
                        alignStartIdx = i
                        timgs.append(imgName)
                        self.skyName0 = tcatParm[4]
                        if startIdx==0:
                            newSky = True
                            print("doCombine %d: new sky: %s, %s, %s"%(i, self.skyName0, skyName, imgName))
                    else:
                        if skyName==self.skyName0:
                            timgs.append(imgName)
                            newSky = False
                        else: #change sky
                            alignStartIdx = i
                            timgs = []
                            timgs.append(imgName)   #G021_tom_objt_190109T13531492.fit , "%s_cmb%03d.fit"%(imgNames[0].split('.')[0], len(imgNames)) 
                            self.skyName0 = skyName
                            print("doCombine %d: skyName change from %s to %s, skip this loop."%(i, self.skyName0, skyName))
                            self.cmbIdx = i-1
                            newSky = True
                            print("doCombine %d: doCombine, new sky: %s, %s, %s"%(i, self.skyName0, skyName, imgName))
                            
                    if newSky:
                        dateStr = imgName.split('_')[3][:6]
                        crossTaskName = "%s_%s_%s_C%03d"%(dateStr, camName, skyName, cmbNum)
                        if runName!='p1':
                            crossTaskName = "%s_%s"%(crossTaskName, runName)
                        print("doCombine %d: register crossTask: %s"%(i, crossTaskName))
                        crossMethod = '1'
                        imgDiff.ot2Classifier.crossTaskCreate(camName, crossTaskName, crossMethod, dateStr, crossTaskParms, imgDiff.tools.serverIP)
                            
                    if len(timgs)==cmbNum:
                        print("doCombine %d: already stack %dth(%d) image, start superCombine"%(i, len(timgs), cmbNum))
                        self.cmbIdx = i
                        timgs = []
                    #else:
                    #    print("doCombine %d: wait %dth(%d) image"%(i, len(timgs), cmbNum))
                        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
            
        self.cmbRunning = 0
        
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
                        tmplParms = diffTmplMap[skyName]
                        status = tmplParms[0]
                        if status=='1':
                            self.diffIdx = i
                            print("doDiff %d: %s, sky=%s"%(i, imgName, skyName))
                            isSuccess = imgDiff.diffImage(imgName, tmplParms)
                            if isSuccess:
                                print("doDiff %d: %s %s diff success"%(i, camName, imgName))
                                diffImgList.append(tcatParm)
                        else:
                            print("doDiff %d: wait template"%(i))
                            break
                    else:
                        print("doDiff %d: %s %s cannot find template"%(i, skyName, imgName))
                        break
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
            
        self.diffRunning = 0
            
    def doRecognitionAndUpload(self, camName, diffImgList, diffTmplMap, imgDiff, runName):
        
        self.recgRunning = 1
        tNum = len(diffImgList)
        lastIdx = self.recgIdx
        print("doRecognitionAndUpload: array has %d images, idx=%d"%(tNum, self.recgIdx))
        
        if tNum-1>lastIdx:
            for i in range(lastIdx+1, tNum):
                try:
                    tcatParm = diffImgList[i]
                    skyName = tcatParm[4]
                    imgName = tcatParm[2]  #G021_tom_objt_190109T13531492.fit , "%s_cmb%03d.fit"%(imgNames[0].split('.')[0], len(imgNames))
                    print("doRecognitionAndUpload %d: %s, sky=%s"%(i, imgName, skyName))
    
                    if skyName in diffTmplMap:
                        self.recgIdx = i
                        tmplParms = diffTmplMap[skyName]
                        imgDiff.classifyAndUpload(imgName, tmplParms, runName, skyName, tcatParm)
                    else:
                        imgDiff.log.warn("doRecognitionAndUpload %d: %s %s cannot find template"%(i, skyName, imgName))
                        #break
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
            
        self.recgRunning = 0
    
    def mainControl(self, camName, runName = 'p1', destDir='/data/gwac_diff_xy', toolPath='/home/gwac/img_diff_xy/image_diff'):
        
        #os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
        #os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
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
        imgDiff.sendMsg(tStr)
        
        #dataPath = '/home/xy/work/imgDiffTest2/fits/190128_G004_044'
        
        #
        #processRecord = '/home/xy/work/imgDiffTest3/log/G004_044.log'
        #os.system("rm -rf %s"%(processRecord))
        
        #sexLock=Lock()
        self.loopNum = 1
        while True:
            
            try:
                curUtcDateTime = datetime.utcnow()
                tDateTime = datetime.utcnow()
                startDateTime = tDateTime.replace(hour=9, minute=30, second=0)  #9=17  1=9
                endDateTime = tDateTime.replace(hour=9, minute=30, second=10)  #22=6    8=16
                remainSeconds1 = (startDateTime - curUtcDateTime).total_seconds()
                remainSeconds2 = (endDateTime - curUtcDateTime).total_seconds()
                if remainSeconds1<0 and remainSeconds2>0:
                    
                    if os.path.exists(dataDest0):
                        os.system("rm -rf %s"%(dataDest0))
                    
                    self.initData()
                    dateStr = datetime.strftime(datetime.utcnow(), "%Y%m%d")
                    dataDest0 = "%s/data/%s_%s"%(destDir, dateStr, runName)
                    if not os.path.exists(dataDest0):
                        os.system("mkdir -p %s"%(dataDest0))
                    imgDiff.reInitDataDir(dataDest0)
                    tStr = "%s: combine diff reInit data"%(camName)
                    print(tStr)
                    imgDiff.log.info(tStr)
                    imgDiff.sendMsg(tStr)
                    time.sleep(10)
            
            except Exception as e:
                tstr = traceback.format_exc()
                print("combine diff reInit data error....")
                print(tstr)
                time.sleep(10)
                
            try:
                print("\n\nmain loop %d****************"%(self.loopNum))
                
                self.srcExtract(camName, self.catList, self.alignTmplMap, imgDiff, logDest0, runName)
                self.getAlignTemplate(camName, self.catList, self.alignTmplMap, imgDiff)
                self.doAlign(camName, self.catList, self.alignTmplMap, self.alignList, imgDiff)
                self.doDiff(camName, self.alignList, self.alignTmplMap, imgDiff, self.diffImgList)

                self.loopNum = self.loopNum + 1
                
                time.sleep(1)
            except Exception as e:
                tstr = traceback.format_exc()
                print("Scheduling main error....")
                print(tstr)
                time.sleep(10)
        
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    if len(sys.argv)==3:
        camName = sys.argv[1]
        runName = sys.argv[2]
        #destDir = '/home/xy/work/imgDiffTest3'
        #toolPath = '/home/xy/Downloads/myresource/deep_data2/image_diff'
        destDir = '/data/gwac_diff_xy'
        toolPath = '/home/gwac/img_diff_xy/image_diff3_minorplanet'
        if len(camName)==4:
            bdiff = BatchImageDiff()
            bdiff.mainControl(camName, runName, destDir, toolPath)
        else:
            print("error: camera name must like G021")
    else:
        print("run: python Scheduling.py cameraName(G021) runName(p2)")