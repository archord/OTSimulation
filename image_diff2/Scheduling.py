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

def srcExtract(camName, catList, imgDiff, isRunning):
    
    isRunning.value = 1
    logDest0 = "/data/gwac_diff_xy/log"
    
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
            
            srcDir= tpath[:(tpath.find(camName)-1)] #/data3/G002_021_190109
            dateStr = srcDir[srcDir.find('G'):] #G002_021_190109
            logfName0 = '%s/%s.log'%(logDest0, dateStr)
            
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
                        catList.append((isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, srcDir))
                    endtime = datetime.now()
                    runTime = (endtime - starttime).seconds
                    imgDiff.log.info("totalTime %d seconds, sky:%d, ffNum:%d, %s"%(runTime, curSkyId, ffNumber, timgName))
                else:
                    imgDiff.log.error("getCat: %s not exist"%(tpath))

        except Exception as e:
            tstr = traceback.format_exc()
            imgDiff.log.error(tstr)

    isRunning.value = 0
    
def srcExtractLocalDir(tpath, camName, catList, imgDiff, isRunning):
    
    isRunning.value = 1
    logDest0 = "/data/gwac_diff_xy/log"
    
    ffId = 0
    tfiles = os.listdir(tpath)
    tfiles.sort()
    print("total read %d files"%(len(tfiles)))
    
    for i, tfile in enumerate(tfiles):
        
        try:
            curFfId = i+1
            ffNumber = 100
            curSkyId = tfile[2]
            timgName = tfile #G021_tom_objt_190109T13531492.fit
            
            srcDir= tpath #/data3/G002_021_190109
            dateStr = srcDir[srcDir.find('G'):] #G002_021_190109
            logfName0 = '%s/%s.log'%(logDest0, dateStr)
            
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
                        catList.append((isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, srcDir))
                    endtime = datetime.now()
                    runTime = (endtime - starttime).seconds
                    imgDiff.log.info("totalTime %d seconds, sky:%d, ffNum:%d, %s"%(runTime, curSkyId, ffNumber, timgName))
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
                            #print('down template')
                            tparms = ('1',tmpls,1) #status, imgList, currentSky image number
                            imgDiff.getAlignTemplate(tparms, skyName)
                            tmplMap[skyName]=tparms 
                        else:
                            #print('make new template')
                            tmplMap[skyName]=('2', [(imgName,)],1) #status, imgList, currentSky image number
                    else:
                        tparms = tmplMap[skyName]
                        status=tparms[0]
                        skyImgNumber = tparms[2]
                        if status=='2':
                            if skyImgNumber==newTmplSelectNum:
                                #imgs = []
                                #for i in range(catNum-newTmplSelectNum, catNum):
                                #    imgs.append((catList[i][2],))
                                tcatParms = catList[catNum-newTmplSelectNum:catNum]
                                tcatParms = np.array(tcatParms)
                                tfwhm = tcatParms[:,5]
                                selCatParms=tcatParms[np.argmin(tfwhm)] #select the image with minFwhm in 10 images
                                tparms = ('2', [(selCatParms[2],)],skyImgNumber+1)
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
                        tmplMap[skyName]=('2', [(imgName,)],1) #status, imgList, currentSky image number
                    else:
                        tparms = tmplMap[skyName]
                        status=tparms[0]
                        skyImgNumber = tparms[2]
                        if status=='2':
                            if skyImgNumber==newTmplSelectNum:
                                #imgs = []
                                #for i in range(catNum-newTmplSelectNum, catNum):
                                #    imgs.append((catList[i][2],))
                                tcatParms = catList[catNum-newTmplSelectNum:catNum]
                                tcatParms = np.array(tcatParms)
                                tfwhm = tcatParms[:,5]
                                selCatParms=tcatParms[np.argmin(tfwhm)] #select the image with minFwhm in 10 images
                                tparms = ('2', [(selCatParms[2],)],skyImgNumber+1)
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
    
def doAlign(camName, catList, tmplMap, tIdx, imgDiff, isRunning):
    
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
                        tIdx.value = i
                        tmplParms = tmplMap[skyName]
                        isSuccess = imgDiff.alignImage(srcDir, imgName, tmplParms)
                        if isSuccess:
                            imgDiff.log.info("%s %s align success"%(camName, imgName))
                    else:
                        imgDiff.log.warn("%s %s cannot find template"%(skyName, imgName))
                        break
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
        
    isRunning.value = 0
        
def doCombine(camName, catList, tmplMap, tIdx, imgDiff, cmbImgList, isRunning, cmbNum=5):
    
    isRunning.value = 1
    lastIdx = tIdx.value
    catNum = len(catList)

    startIdx = lastIdx+1
    if catNum>=startIdx+cmbNum:
        timgs = []
        for i in range(lastIdx+1, catNum):
            try:
                tcatParm = catList[i]
                skyName = tcatParm[4]
                imgName = tcatParm[2]
                
                if len(timgs)==0:
                    timgs.append(imgName)
                    skyName0 = tcatParm[4]
                else:
                    if skyName==skyName0:
                        timgs.append(imgName)
                    else: #change sky
                        timgs = []
                        timgs.append(imgName)
                        skyName0 = skyName
                        imgDiff.log.warn("skyName change from %s to %s, skip this loop."%(skyName0, skyName))
                        tIdx.value = i-1
                        
                if len(timgs)==cmbNum:
                    cmbName = imgDiff.superCombine(timgs)
                    tcatParm = catList[startIdx]
                    tcatParm[2]=cmbName
                    cmbImgList.append(tcatParm) #(isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, srcDir)
                    imgDiff.log.info("%s combine %s."%(camName, cmbName))
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
                isSuccess, skyName, starNum, fwhmMean, bgMean = imgDiff.getCat(imgDiff.cmbDir, cmbImgName, imgDiff.cmbCatDir)
                if isSuccess: #we can add more filter condition, to remove bad images
                    cmbCatList.append((isSuccess, ffId, cmbImgName, starNum, skyName, fwhmMean, bgMean, skyId, imgDiff.cmbDir))
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
                            tmplParms[2] = 1
                            if status=='1':
                                diffTmplMap[skyName]=tmplParms
                            else:
                                tmplParms[0]='3'
                                diffTmplMap[skyName]=tmplParms
                        else:
                            tmplParms = diffTmplMap[skyName]
                            skyImgNumber = tmplParms[2]
                            tmplParms[2] = skyImgNumber+1
                            status=tmplParms[0]
                            
                            if status=='3': #redo template
                                if skyImgNumber==newTmplSelectNum:
                                    tcatParms = cmbCatList[catNum-newTmplSelectNum:catNum]
                                    tcatParms = np.array(tcatParms)
                                    tfwhm = tcatParms[:,5]
                                    selCatParms=tcatParms[np.argmin(tfwhm)] #select the image with minFwhm in 10 images
                                    tparms = ('2', [(selCatParms[2],)],skyImgNumber+1)
                                    runSuccess = imgDiff.getDiffTemplate(tparms, skyName, selCatParms)
                                    if runSuccess:
                                        diffTmplMap[skyName] = tparms
                                    else:
                                        diffTmplMap[skyName] = tmplParms
                                else:
                                    diffTmplMap[skyName] = tmplParms
                            elif status=='2':
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
    if tNum-1>lastIdx:
        for i in range(lastIdx+1, tNum):
            try:
                tcatParm = cmbImgList[i]
                skyName = tcatParm[4]
                imgName = tcatParm[2]

                if skyName in diffTmplMap:
                    tIdx.value = i
                    tmplParms = diffTmplMap[skyName]
                    isSuccess = imgDiff.diffImage(imgName, tmplParms)
                    if isSuccess:
                        imgDiff.log.info("%s %s diff success"%(camName, imgName))
                        diffImgList.append(tcatParm)
                else:
                    imgDiff.log.warn("%s %s cannot find template"%(skyName, imgName))
                    break
    
            except Exception as e:
                tstr = traceback.format_exc()
                imgDiff.log.error(tstr)
        
    isRunning.value = 0
        
def doRecognitionAndUpload(camName, diffImgList, diffTmplMap, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    tNum = len(diffImgList)
    lastIdx = tIdx.value
    if tNum-1>lastIdx:
        for i in range(lastIdx+1, tNum):
            try:
                tcatParm = diffImgList[i]
                skyName = tcatParm[4]
                imgName = tcatParm[2]

                if skyName in diffTmplMap:
                    tIdx.value = i
                    tmplParms = diffTmplMap[skyName]
                    imgDiff.classifyAndUpload(imgName, tmplParms)
                else:
                    imgDiff.log.warn("%s %s cannot find template"%(skyName, imgName))
                    break
    
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
            
    def mainControl(self, camName, destDir='/data/gwac_diff_xy', toolPath='/home/gwac/img_diff_xy/image_diff'):
        
        dateStr = datetime.strftime(datetime.utcnow(), "%Y%m%d")
        dataDest0 = "%s/data/%s"%(destDir, dateStr)
        logDest0 = "%s/log"%(destDir)
        if not os.path.exists(logDest0):
            os.system("mkdir -p %s"%(logDest0))
        if not os.path.exists(dataDest0):
            os.system("mkdir -p %s"%(dataDest0))
        
        tools = AstroTools(toolPath)
        
        imgDiff = GWACDiff(camName, dataDest0, tools)
        tStr = "start diff..."
        imgDiff.log.info(tStr)
        imgDiff.sendMsg(tStr)
        
        dataPath = '/home/xy/work/imgDiffTest2/fits/190128_G004_044'
        
        loopNum = 1
        while True:
            
            curUtcDateTime = datetime.utcnow()
            tDateTime = datetime.utcnow()
            
            startDateTime = tDateTime.replace(hour=9, minute=0, second=0)  #9=17  1=9
            endDateTime = tDateTime.replace(hour=22, minute=0, second=0)  #22=6    8=16
            remainSeconds1 = (startDateTime - curUtcDateTime).total_seconds()
            remainSeconds2 = (endDateTime - curUtcDateTime).total_seconds()
            
            '''
            def srcExtract(camName, catList, imgDiff, isRunning)
            def getAlignTemplate(camName, catList, alignTmplMap, tIdx, imgDiff, isRunning)
            def doAlign(camName, catList, alignTmplMap, tIdx, imgDiff, isRunning)
            def doCombine(camName, catList, alignTmplMap, tIdx, imgDiff, cmbImgList, isRunning, cmbNum=5)
            def srcExtractCombine(camName, cmbImgList, cmbCatList, tIdx, imgDiff, isRunning)
            def getDiffTemplate(camName, cmbCatList, alignTmplMap, diffTmplMap, tIdx, imgDiff, isRunning)
            def doDiff(camName, cmbImgList, diffTmplMap, tIdx, imgDiff, diffImgList, isRunning)
            def doRecognitionAndUpload(camName, diffImgList, diffTmplMap, tIdx, imgDiff, isRunning):
            '''

            #if not (remainSeconds1<0 and remainSeconds2>0):
            if True:
                tIdx1 = loopNum%5
                if tIdx1==1 and self.catRunning.value==0:  #cat
                    catJob = Process(target=srcExtractLocalDir, args=(dataPath, camName, self.catList, imgDiff, self.catRunning))
                    catJob.start()
                    '''
                tIdx2 = loopNum%10
                if tIdx2==0 and self.alignTmplRunning==0: #template
                    alignTmplJob = Process(target=getAlignTemplateLocal, args=(
                            camName, self.catList, self.alignTmplMap, self.alignTmplIdx, imgDiff, self.alignTmplRunning))
                    alignTmplJob.start()
                    
                tIdx3 = loopNum%2
                if self.alignRunning==0: #align
                    alignJob = Process(target=doAlign, args=(
                            camName, self.catList, self.alignTmplMap, self.alignIdx, imgDiff,  self.alignRunning))
                    alignJob.start()
                    
                tIdx4 = loopNum%2
                if self.cmbRunning==0: #combine5
                    cmbJob = Process(target=doCombine, args=(
                            camName, self.catList, self.alignTmplMap, self.cmbIdx, imgDiff, self.cmbImgList,  self.cmbRunning))
                    cmbJob.start()
                 
                tIdx5 = loopNum%2
                if self.cmbCatRunning==0: #cat of combine5
                    cmbCatJob = Process(target=srcExtractCombine, args=(
                            camName, self.cmbImgList, self.cmbCatList, self.cmbCatIdx, imgDiff, self.cmbCatRunning))
                    cmbCatJob.start()
                    
                tIdx6 = loopNum%10
                if tIdx6==0 and self.diffTmplRunning==0: #cat of combine5
                    diffTmplJob = Process(target=getDiffTemplate, args=(
                            camName, self.cmbCatList, self.alignTmplMap, self.diffTmplMap, self.diffTmplIdx, imgDiff, self.cmbCatRunning))
                    diffTmplJob.start()
                    
                if self.diffRunning==0: #diff
                    diffJob = Process(target=doDiff, args=(
                            camName, self.cmbImgList, self.diffTmplMap, self.diffIdx, imgDiff, self.diffImgList, self.diffRunning))
                    diffJob.start()
                    '''
                    '''
                if self.recgRunning==0: #recognition
                    recgJob = Process(target=doRecognitionAndUpload, args=(
                            camName, self.diffImgList, self.diffTmplMap, self.recgIdx, imgDiff, self.recgRunning))
                    recgJob.start()
                 '''   
                loopNum = loopNum + 1
                if loopNum>10:
                    break
                
                time.sleep(1)
            else:
                loopNum = 1
                time.sleep(10*60)
        
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    if len(sys.argv)==2:
        camName = sys.argv[1]
        destDir = '/home/xy/work/imgDiffTest3'
        toolPath = '/home/xy/Downloads/myresource/deep_data2/image_diff'
        if len(camName)==4:
            bdiff = BatchImageDiff()
            bdiff.mainControl(camName, destDir, toolPath)
        else:
            print("error: camera name must like G021")
    else:
        print("run: python BatchDiff.py cameraName(G021)")