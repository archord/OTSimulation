# -*- coding: utf-8 -*-

from multiprocessing import Manager,Process,Lock
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

def srcExtract(camName, catList, imgDiff, logDestDir, isRunning):
    
    isRunning.value = 1
    
    catNum = len(catList)
    if catNum>0:
        lastCat = catList[catNum-1]
        ffId = lastCat[1]
    else:
        ffId = 0
        
    query = QueryData()
    tfiles = query.getFileList(camName, ffId)
    #print(tfiles)
    for tfile in tfiles:
        
        try:
            curFfId = tfile[0]
            ffNumber = tfile[1]
            curSkyId = tfile[2]
            timgName = tfile[3] #G021_tom_objt_190109T13531492.fit
            tpath = tfile[4] #/data3/G002_021_190109/G021_tom_objt_190109T13531492.fit
            print("srcExtract: %s"%(tpath))
            
            srcDir= tpath[:(tpath.find(camName)-1)] #/data3/G002_021_190109
            dateStr = srcDir[srcDir.find('G'):] #G002_021_190109
            logfName0 = '%s/%s.log'%(logDestDir, dateStr)
            
            if ffId==0:
                if os.path.exists(logfName0) and os.stat(logfName0).st_size > 0:
                    tlastLine = getLastLine(logfName0)
                    if len(tlastLine)>2:
                        ffId=int(tlastLine.strip())

            if curFfId>ffId:
                ffId=curFfId
                
                logfile0 = open(logfName0, 'a')
                logfile0.write("\n\n%d\n"%(ffId))
                logfile0.close()
                
                tpathfz = "%s.fz"%(tpath)
                if os.path.exists(tpath) or os.path.exists(tpathfz):
                    starttime = datetime.now()
                    isSuccess, skyName, starNum, fwhmMean, bgMean = imgDiff.getCat(srcDir, timgName, imgDiff.catDir)
                    if isSuccess: #we can add more filter condition, to remove bad images
                        catList.append([isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, srcDir])
                    endtime = datetime.now()
                    runTime = (endtime - starttime).seconds
                    imgDiff.log.info("totalTime %d seconds, sky:%d, ffNum:%d, %s"%(runTime, curSkyId, ffNumber, timgName))
                else:
                    imgDiff.log.error("getCat: %s not exist"%(tpath))

        except Exception as e:
            tstr = traceback.format_exc()
            imgDiff.log.error(tstr)

    isRunning.value = 0
    
def srcExtractLocalDir(tpath, camName, catList, imgDiff, logDestDir, isRunning):
    
    isRunning.value = 1
    #print("srcExtractLocalDir: catNum=%d"%(len(catList)))
    
    ffId = 0
    tfiles = os.listdir(tpath)
    tfiles.sort()
    #print("total read %d files"%(len(tfiles)))
    
    runIdx = 1
    for i, tfile in enumerate(tfiles):
        if runIdx>10:
            break
        try:
            curFfId = i+1
            ffNumber = 100
            curSkyId = 0
            timgName = tfile #G021_tom_objt_190109T13531492.fit
            
            srcDir= tpath #/data3/G002_021_190109 /home/xy/work/imgDiffTest2/fits/190128_G004_044
            dateStr = srcDir[srcDir.find('G'):] #G002_021_190109
            logfName0 = '%s/%s.log'%(logDestDir, dateStr)
            
            if ffId==0:
                if os.path.exists(logfName0) and os.stat(logfName0).st_size > 0:
                    tlastLine = getLastLine(logfName0)
                    #print("tlastLine %s"%(tlastLine))
                    if len(tlastLine)>=2:
                        ffId=int(tlastLine.strip())
                        #print("read ffId %d"%(ffId))

            if curFfId>ffId:
                runIdx=runIdx+1
                ffId=curFfId
                
                logfile0 = open(logfName0, 'a')
                logfile0.write("\n\n%d\n"%(ffId))
                logfile0.close()
                
                tpathfz = "%s.fz"%(tpath)
                if os.path.exists(tpath) or os.path.exists(tpathfz):
                    starttime = datetime.now()
                    isSuccess, skyName, starNum, fwhmMean, bgMean = imgDiff.getCat(srcDir, timgName, imgDiff.catDir)
                    if isSuccess: #we can add more filter condition, to remove bad images
                        catList.append([isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, srcDir])
                    endtime = datetime.now()
                    runTime = (endtime - starttime).seconds
                    imgDiff.log.info("srcExtractLocalDir, totalTime %d seconds, sky:%d, ffNum:%d, %s"%(runTime, curSkyId, ffNumber, timgName))
                else:
                    imgDiff.log.error("getCat: %s not exist"%(tpath))

        except Exception as e:
            tstr = traceback.format_exc()
            imgDiff.log.error(tstr)

    isRunning.value = 0
    
def getAlignTemplate(camName, catList, tmplMap, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    catNum = len(catList)
    newTmplSelectNum = 10
    if catNum>=1:
        lastIdx = tIdx.value
        if catNum-1>lastIdx:
            for i in range(lastIdx+1, catNum):
                try:
                    tcatParm = catList[i]
                    skyId = tcatParm[7]
                    skyName = tcatParm[4]
                    imgName = tcatParm[2]
                    
                    if skyName not in tmplMap:
                        query = QueryData()
                        tmpls = query.getTmplList(camName, skyId)
                        if len(tmpls)>0:
                            tparms = ['1',tmpls,1] #status, imgList, currentSky image number
                            imgDiff.getAlignTemplate(tparms, skyName)
                            tmplMap[skyName]=tparms 
                        else:
                            #print('make new template')
                            tmplMap[skyName]=['2', [],1] #status, imgList, currentSky image number
                    else:
                        tparms = tmplMap[skyName]
                        status=tparms[0]
                        skyImgNumber = tparms[2]
                        if status=='2':
                            if skyImgNumber==newTmplSelectNum:
                                tcatParms = catList[catNum-newTmplSelectNum:catNum]
                                tcatParms = np.array(tcatParms)
                                tfwhm = tcatParms[:,5]
                                selCatParms=tcatParms[np.argmin(tfwhm)] #select the image with minFwhm in 10 images
                                tparms = ['2', [(selCatParms[2],)],skyImgNumber+1]
                                imgDiff.getAlignTemplate(tparms, skyName)
                                tmplMap[skyName] = tparms
                            else: #if skyImgNumber<newTmplSelectNum
                                tparms[2] = skyImgNumber+1
                                tmplMap[skyName] = tparms
                    tIdx.value = i
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
    isRunning.value = 0
    
def getAlignTemplateLocal(camName, catList, tmplMap, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    catNum = len(catList)
    
    newTmplSelectNum = 10
    if catNum>=1:
        lastIdx = tIdx.value
        if catNum-1>lastIdx:
            for i in range(lastIdx+1, catNum):
                try:
                    tcatParm = catList[i]
                    skyId = tcatParm[7]
                    skyName = tcatParm[4]
                    imgName = tcatParm[2]
                    
                    if skyName not in tmplMap:
                        tmplMap[skyName]=['2', [],1] #status, imgList, currentSky image number
                    else:
                        tparms = tmplMap[skyName]
                        status=tparms[0]
                        skyImgNumber = tparms[2]
                        if status=='2':
                            if skyImgNumber==newTmplSelectNum:
                                tcatParms = catList[catNum-newTmplSelectNum:catNum]
                                tcatParms = np.array(tcatParms)
                                tfwhm = tcatParms[:,5]
                                selCatParms=tcatParms[np.argmin(tfwhm)] #select the image with minFwhm in 10 images
                                tparms = ['2', [(selCatParms[2],)],skyImgNumber+1]
                                imgDiff.getAlignTemplate(tparms, skyName)
                                tmplMap[skyName] = tparms
                            else: #if skyImgNumber<newTmplSelectNum
                                tmplMap[skyName] = ['2', tparms[1], skyImgNumber+1]
                    tIdx.value = i
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
    isRunning.value = 0
    
def doAlign(camName, catList, tmplMap, tIdx, alignList, imgDiff, isRunning):
    
    isRunning.value = 1
    catNum = len(catList)
    if catNum>1:
        lastIdx = tIdx.value
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
                            tIdx.value = i
                            isSuccess = imgDiff.alignImage(srcDir, imgName, tmplParms)
                            if isSuccess:
                                alignList.append(tcatParm)
                                imgDiff.log.info("%s %s align success"%(camName, imgName))
                        else:
                            #print("doAlign wait template")
                            break
                    else:
                        imgDiff.log.warn("doAlign %s %s cannot find template"%(skyName, imgName))
                        break
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
        
    isRunning.value = 0
        
def doCombine(camName, alignList, tmplMap, tIdx, imgDiff, cmbImgList, isRunning, cofParms, runName, cmbNum=5):
    
    isRunning.value = 1
    lastIdx = tIdx.value
    catNum = len(alignList)
    #print("doCombine catNum=%d, lastIdx=%d"%(catNum, lastIdx))

    newSky = False
    startIdx = lastIdx+1
    if catNum>=startIdx+cmbNum:
        timgs = []
        for i in range(lastIdx+1, catNum):
            try:
                tcatParm = alignList[i]
                skyName = tcatParm[4]
                imgName = tcatParm[2]
                                    
                if len(timgs)==0:
                    timgs.append(imgName)
                    skyName0 = tcatParm[4]
                    if startIdx==0:
                        newSky = True
                        print("%d, %s, %s, %s"%(i, skyName0, skyName, imgName))
                else:
                    if skyName==skyName0:
                        timgs.append(imgName)
                        newSky = False
                    else: #change sky
                        timgs = []
                        timgs.append(imgName)   #G021_tom_objt_190109T13531492.fit , "%s_cmb%03d.fit"%(imgNames[0].split('.')[0], len(imgNames)) 
                        skyName0 = skyName
                        imgDiff.log.warn("skyName change from %s to %s, skip this loop."%(skyName0, skyName))
                        tIdx.value = i-1
                        newSky = True
                        print("%d, %s, %s, %s"%(i, skyName0, skyName, imgName))
                        
                if newSky:
                    dateStr = imgName.split('_')[3][:6]
                    crossTaskName = "%s_%s_C%03d"%(dateStr, camName, cmbNum)
                    if runName!='p1':
                        crossTaskName = "%s_%s"%(crossTaskName, runName)
                    print("doCombine %s"%(crossTaskName))
                    crossMethod = '1'
                    imgDiff.ot2Classifier.crossTaskCreate(crossTaskName, crossMethod, dateStr, cofParms, imgDiff.tools.serverIP)
                        
                if len(timgs)==cmbNum:
                    cmbName = imgDiff.superCombine(timgs)
                    if len(cmbName)>0:
                        tcatParm = alignList[startIdx]
                        tcatParm[2]=cmbName
                        cmbImgList.append(tcatParm) #(isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, srcDir)
                        #imgDiff.log.info("%s combine %s."%(camName, cmbName))
                    tIdx.value = i
                    timgs = []
                    
            except Exception as e:
                tstr = traceback.format_exc()
                imgDiff.log.error(tstr)
        
    isRunning.value = 0
    
def srcExtractCombine(camName, cmbImgList, cmbCatList, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    catNum = len(cmbImgList)
    lastIdx = tIdx.value
    
    if catNum>1 and catNum-1>lastIdx:
        for i in range(lastIdx+1, catNum):
            try:
                tparm = cmbImgList[i]
                cmbImgName = tparm[2]
                skyId = tparm[7]
                skyName = tparm[4]
                ffId = tparm[1]
                
                starttime = datetime.now()
                isSuccess, skyName, starNum, fwhmMean, bgMean = imgDiff.getCat(imgDiff.cmbDir, cmbImgName, imgDiff.cmbCatDir, 'cmb')
                if isSuccess: #we can add more filter condition, to remove bad images
                    cmbCatList.append([isSuccess, ffId, cmbImgName, starNum, skyName, fwhmMean, bgMean, skyId, imgDiff.cmbDir])
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                imgDiff.log.info("totalTime %d seconds, sky:%d, %s"%(runTime, skyId, cmbImgName))
                
                tIdx.value = i
            except Exception as e:
                tstr = traceback.format_exc()
                imgDiff.log.error(tstr)

    isRunning.value = 0
    
def getDiffTemplate(camName, cmbCatList, alignTmplMap, diffTmplMap, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    newTmplSelectNum = 10
    #newTmplSelectNum = 2
    catNum = len(cmbCatList)
    if catNum>=newTmplSelectNum:
        lastIdx = tIdx.value
        if catNum-1>lastIdx:
            for i in range(lastIdx+1, catNum):
                try:
                    tcatParm = cmbCatList[i]
                    skyName = tcatParm[4]
                    
                    if skyName in alignTmplMap:
                        tmplParms = alignTmplMap[skyName]
                        skyImgNumber = tmplParms[2]
                        status = tmplParms[0]
                        if skyName not in diffTmplMap:
                            print("getDiffTemplate: already has template")
                            tmplParms[2] = 1
                            if status=='1':
                                #print("alignTmplMap")
                                #print(alignTmplMap)
                                print("getDiffTemplate: template is history good single frame, sky=%s"%(skyName))
                                diffTmplMap[skyName]=tmplParms
                                #print(diffTmplMap)
                            else:
                                print("getDiffTemplate: use local rebuilt template")
                                tmplParms[0]='3'
                                diffTmplMap[skyName]=tmplParms
                        else:
                            tmplParms = diffTmplMap[skyName]
                            skyImgNumber = tmplParms[2]
                            status = tmplParms[0]
                            tmplParms = [status, tmplParms[1],skyImgNumber+1]
                            
                            if status=='3': #redo template
                                if skyImgNumber==newTmplSelectNum:
                                    print("getDiffTemplate: start build diff template")
                                    tcatParms = cmbCatList[catNum-newTmplSelectNum:catNum]
                                    tcatParms = np.array(tcatParms)
                                    tfwhm = tcatParms[:,5]
                                    selCatParms=tcatParms[np.argmin(tfwhm)] #select the image with minFwhm in 10 images
                                    tparms = ['2', [(selCatParms[2],)],skyImgNumber+1]
                                    
                                    runSuccess = imgDiff.getDiffTemplate(tparms, skyName, selCatParms)
                                    if runSuccess:
                                        diffTmplMap[skyName] = tparms
                                    else:
                                        diffTmplMap[skyName] = tmplParms
                                    
                                else:
                                    print("getDiffTemplate: use local rebuilt template, waiting %d images"%(skyImgNumber))
                                    diffTmplMap[skyName] = tmplParms
                                    #print("getDiffTemplate wait %d combine image"%(newTmplSelectNum))
                            elif status=='2':
                                print("getDiffTemplate: use local rebuilt template, select local")
                                diffTmplMap[skyName] = tmplParms
                                #if skyImgNumber>50, update diff template
                                
                    tIdx.value = i
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
    isRunning.value = 0
    
def doDiff(camName, cmbImgList, diffTmplMap, tIdx, imgDiff, diffImgList, isRunning):
    
    isRunning.value = 1
    tNum = len(cmbImgList)
    lastIdx = tIdx.value
    #print("doDiff %d:%d"%(tNum, lastIdx))
    if tNum-1>lastIdx:
        for i in range(lastIdx+1, tNum):
            try:
                tcatParm = cmbImgList[i]
                skyName = tcatParm[4]
                imgName = tcatParm[2]
                #print("start doDiff %s"%(imgName))

                if skyName in diffTmplMap:
                    tIdx.value = i
                    tmplParms = diffTmplMap[skyName]
                    status = tmplParms[0]
                    if status=='2' or status=='1':
                        #print("has template doDiff %s, sky=%s"%(imgName, skyName))
                        #print(diffTmplMap)
                        #print(tmplParms)
                        isSuccess = imgDiff.diffImage(imgName, tmplParms)
                        if isSuccess:
                            imgDiff.log.info("%s %s diff success"%(camName, imgName))
                            diffImgList.append(tcatParm)
                    else:
                        print("doDiff wait template")
                        break
                else:
                    imgDiff.log.warn("doDiff %s %s cannot find template"%(skyName, imgName))
                    break
    
            except Exception as e:
                tstr = traceback.format_exc()
                imgDiff.log.error(tstr)
        
    isRunning.value = 0
        
def doRecognitionAndUpload(camName, diffImgList, diffTmplMap, tIdx, imgDiff, isRunning, runName):
    
    isRunning.value = 1
    tNum = len(diffImgList)
    lastIdx = tIdx.value
    if tNum-1>lastIdx:
        for i in range(lastIdx+1, tNum):
            try:
                tcatParm = diffImgList[i]
                skyName = tcatParm[4]
                imgName = tcatParm[2]  #G021_tom_objt_190109T13531492.fit , "%s_cmb%03d.fit"%(imgNames[0].split('.')[0], len(imgNames))

                if skyName in diffTmplMap:
                    tIdx.value = i
                    tmplParms = diffTmplMap[skyName]
                    imgDiff.classifyAndUpload(imgName, tmplParms, runName)
                else:
                    imgDiff.log.warn("doRecognitionAndUpload %s %s cannot find template"%(skyName, imgName))
                    #break
    
            except Exception as e:
                tstr = traceback.format_exc()
                imgDiff.log.error(tstr)
        
    isRunning.value = 0
        
class BatchImageDiff(object):
    
    def __init__(self):
        self.dataMgr = Manager()
        self.catList = self.dataMgr.list()
        self.catQueue = self.dataMgr.Queue()
        self.alignTmplMap = self.dataMgr.dict()
        self.alignList = self.dataMgr.list()
        self.cmbImgList = self.dataMgr.list()
        self.cmbCatList = self.dataMgr.list()
        self.diffTmplMap = self.dataMgr.dict()
        self.diffImgList = self.dataMgr.list()

        self.alignTmplIdx = self.dataMgr.Value('i', -1)
        self.alignIdx = self.dataMgr.Value('i', -1)
        self.cmbIdx = self.dataMgr.Value('i', -1)
        self.cmbCatIdx = self.dataMgr.Value('i', -1)
        self.diffTmplIdx = self.dataMgr.Value('i', -1)
        self.diffIdx = self.dataMgr.Value('i', -1)
        self.recgIdx = self.dataMgr.Value('i', -1)
        
        self.catRunning = self.dataMgr.Value('i', 0)
        self.alignTmplRunning = self.dataMgr.Value('i', 0)
        self.alignRunning = self.dataMgr.Value('i', 0)
        self.cmbRunning = self.dataMgr.Value('i', 0)
        self.cmbCatRunning = self.dataMgr.Value('i', 0)
        self.diffTmplRunning = self.dataMgr.Value('i', 0)
        self.diffRunning = self.dataMgr.Value('i', 0)
        self.recgRunning = self.dataMgr.Value('i', 0)
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
            
    def mainControl(self, camName, runName = 'p1', destDir='/data/gwac_diff_xy', toolPath='/home/gwac/img_diff_xy/image_diff'):
        
        #os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
        #os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        dateStr = datetime.strftime(datetime.utcnow(), "%Y%m%d")
        dataDest0 = "%s/data/%s_%s"%(destDir, dateStr, runName)
        logDest0 = "%s/log_%s"%(destDir, runName)
        if not os.path.exists(logDest0):
            os.system("mkdir -p %s"%(logDest0))
        if not os.path.exists(dataDest0):
            os.system("mkdir -p %s"%(dataDest0))
        
        tools = AstroTools(toolPath)
        
        imgDiff = GWACDiff(camName, dataDest0, tools)
        tStr = "start diff..."
        imgDiff.log.info(tStr)
        imgDiff.sendMsg(tStr)
        
        #dataPath = '/home/xy/work/imgDiffTest2/fits/190128_G004_044'
        
        #
        #processRecord = '/home/xy/work/imgDiffTest3/log/G004_044.log'
        #os.system("rm -rf %s"%(processRecord))
        
        #sexLock=Lock()
        loopNum = 1
        while True:
            
            try:
            
                tIdx1 = loopNum%5
                ''' '''
                if tIdx1==1 and self.catRunning.value==0:  #cat
                        #catJob = Process(target=srcExtractLocalDir, args=(dataPath, camName, self.catList, imgDiff, logDest0, self.catRunning))
                        catJob = Process(target=srcExtract, args=(camName, self.catList, imgDiff, logDest0, self.catRunning))
                        catJob.start()
                
                tIdx2 = loopNum%15
                #tIdx2 = loopNum%5
                if tIdx2==0 and self.alignTmplRunning.value==0: #template getAlignTemplateLocal
                        alignTmplJob = Process(target=getAlignTemplate, args=(
                                camName, self.catList, self.alignTmplMap, self.alignTmplIdx, imgDiff, self.alignTmplRunning))
                        alignTmplJob.start()
                    
                if self.alignRunning.value==0: #align
                    alignJob = Process(target=doAlign, args=(
                            camName, self.catList, self.alignTmplMap, self.alignIdx, self.alignList, imgDiff,  self.alignRunning))
                    alignJob.start()
                    
                if self.cmbRunning.value==0: #combine5
                    #print("%d cmbJob is not running, catNum=%d, alignNum=%d, cmbIdx=%d"%(loopNum, len(self.catList), len(self.alignList), self.cmbIdx.value))
                    cmbJob = Process(target=doCombine, args=(
                            camName, self.alignList, self.alignTmplMap, self.cmbIdx, 
                            imgDiff, self.cmbImgList,  self.cmbRunning, self.crossTaskParms, 5))
                    cmbJob.start()
                #else:
                #    print("%d cmbJob is running"%(loopNum))
                 
                if self.cmbCatRunning.value==0: #cat of combine5
                    cmbCatJob = Process(target=srcExtractCombine, args=(
                            camName, self.cmbImgList, self.cmbCatList, self.cmbCatIdx, imgDiff, self.cmbCatRunning))
                    cmbCatJob.start()
                #else:
                #    print("%d cmbCatJob is running"%(loopNum))      
                
                tIdx6 = loopNum%15
                #tIdx6 = loopNum%1
                if tIdx6==0 and self.diffTmplRunning.value==0: #cat of combine5
                    diffTmplJob = Process(target=getDiffTemplate, args=(
                            camName, self.cmbCatList, self.alignTmplMap, self.diffTmplMap, self.diffTmplIdx, imgDiff, self.diffTmplRunning))
                    diffTmplJob.start()
                #else:
                #    print("%d diffTmplJob is running"%(loopNum))
                    
                
                tIdx7 = loopNum%5
                if tIdx7==0:
                    if self.diffRunning.value==0: #diff
                        #print("%d doDiff start run"%(loopNum))
                        #diffJob = Process(target=doDiff, args=(
                        #        camName, self.cmbImgList, self.diffTmplMap, self.diffIdx, imgDiff, self.diffImgList, self.diffRunning))
                        diffJob = Process(target=doDiff, args=(
                                camName, self.cmbCatList, self.diffTmplMap, self.diffIdx, imgDiff, self.diffImgList, self.diffRunning))
                        diffJob.start()
                    #else:
                    #    print("%d doDiff is running"%(loopNum))
                    
                tIdx8 = loopNum%2
                if tIdx8==0:
                    if self.recgRunning.value==0: #recognition
                        print("%d doRecognitionAndUpload start run"%(loopNum))
                        #recgJob = Process(target=doRecognitionAndUpload, args=(
                        #        camName, self.diffImgList, self.diffTmplMap, self.recgIdx, imgDiff, self.recgRunning))
                        #recgJob.start()
                        doRecognitionAndUpload(camName, self.diffImgList, self.diffTmplMap, self.recgIdx, imgDiff, self.recgRunning)
                    else:
                        print("%d doRecognitionAndUpload is running"%(loopNum))
                   
                loopNum = loopNum + 1
                #if loopNum>4000:
                #    break
                
                time.sleep(1)
                '''
                try:
                    catJob.join()
                    alignJob.join()
                    cmbJob.join()
                except NameError as e:
                    tstr = traceback.format_exc()
                    print("catJob is not defined")
                    print(tstr)
                    '''
            except Exception as e:
                tstr = traceback.format_exc()
                print("Scheduling main error....")
                print(tstr)
                time.sleep(10)
        
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    if len(sys.argv)==2:
        camName = sys.argv[1]
        #destDir = '/home/xy/work/imgDiffTest3'
        #toolPath = '/home/xy/Downloads/myresource/deep_data2/image_diff'
        destDir = '/data/gwac_diff_xy'
        toolPath = '/home/gwac/img_diff_xy/image_diff'
        if len(camName)==4:
            bdiff = BatchImageDiff()
            bdiff.mainControl(camName, destDir, toolPath)
        else:
            print("error: camera name must like G021")
    else:
        print("run: python Scheduling.py cameraName(G021)")