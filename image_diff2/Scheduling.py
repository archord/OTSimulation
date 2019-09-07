# -*- coding: utf-8 -*-

from multiprocessing import Manager,Process,Lock
import time
import traceback
from datetime import datetime
import os

from QueryData import QueryData
from astrotools import AstroTools
from ot2classify import OT2Classify

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
                            tmplMap[skyName]=('1',tmpls,1) #status, imgList, currentSky image number
                            imgDiff.getAlignTemplate(tmplMap[skyName], skyName)
                        else:
                            #print('make new template')
                            tmplMap[skyName]=('2', [(imgName,)],1) #status, imgList, currentSky image number
                    else:
                        tparms = tmplMap[skyName]
                        status=tparms[0]
                        imgNumber = tparms[2]
                        if status=='2' and imgNumber>=newTmplSelectNum:
                            imgs = []
                            for i in range(catNum-newTmplSelectNum, catNum):
                                imgs.append((catList[i][2],))
                            tparms = ('2', imgs,imgNumber)
                            imgDiff.getAlignTemplate(tparms, skyName)
                            tmplMap[skyName] = tparms
                        else:
                            tparms[2] = imgNumber+1
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
    catNum = len(catList)
    if catNum>1 and catNum%cmbNum==0:
        cmbIdx = int(catNum/cmbNum)
        lastIdx = tIdx.value
        if cmbIdx-1>lastIdx:
            for i in range(lastIdx+1, cmbIdx):
                try:
                    changeSky = False
                    startIdx = i*cmbNum
                    endIdx = (i+1)*cmbNum
                    timgs = []
                    for j in range(startIdx, endIdx):
                        tcatParm = catList[j]
                        skyName = tcatParm[4]
                        imgName = tcatParm[2]
                        if len(timgs)==0:
                            timgs.append(imgName)
                            skyName0 = tcatParm[4]
                        else:
                            if skyName==skyName0:
                                timgs.append(imgName)
                            else:
                                changeSky = True
                                imgDiff.log.warn("skyName change from %s to %s, skip this loop."%(skyName0, skyName))
                                break
                    if not changeSky:
                        cmbName = imgDiff.superCombine(timgs)
                        tcatParm = catList[startIdx]
                        tcatParm[2]=cmbName
                        cmbImgList.append(tcatParm) #(isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId, srcDir)
                        imgDiff.log.info("%s combine %s."%(camName, cmbName))
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
        
    isRunning.value = 0
    
def srcExtractCombine(camName, cmbImgList, cmbCatList, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    catNum = len(cmbImgList)
    
    if catNum>1:
        lastIdx = tIdx.value
        if catNum-1>lastIdx:
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
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)

    isRunning.value = 0
    
def getDiffTemplate(camName, cmbCatList, alignTmplMap, diffTmplMap, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    makeTmpl = False
    catNum = len(cmbCatList)
    if catNum>=10:
        lastIdx = tIdx.value
        if catNum-1>lastIdx:
            for i in range(lastIdx+1, catNum):
                try:
                    tcatParm = cmbCatList[i]
                    skyId = tcatParm[7]
                    skyName = tcatParm[4]
                    imgName = tcatParm[2]
                    
                    if (skyName in alignTmplMap) and (skyName not in diffTmplMap):
                        tmplParms = alignTmplMap[skyName]
                        status = tmplParms[0]
                        if status=='1':
                            diffTmplMap[skyName]=tmplParms
                        else:
                            if catNum>=10:
                                imgDiff.getAlignTemplate(alignTmplMap[skyName], skyName)
                            
                        tIdx.value = i
        
                except Exception as e:
                    tstr = traceback.format_exc()
                    imgDiff.log.error(tstr)
    isRunning.value = 0
    
def doDiff(camName, cmbImgList, tmplMap, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    tNum = len(cmbImgList)
    if tNum>1:
        lastIdx = tIdx.value
        if tNum-1>lastIdx:
            for i in range(lastIdx+1, tNum):
                try:
                    tcatParm = cmbImgList[i]
                    skyName = tcatParm[4]
                    imgName = tcatParm[2]
                    srcDir = tcatParm[8]

                    if skyName in tmplMap:
                        tIdx.value = i
                        tmplParms = tmplMap[skyName]
                        status = tmplParms[0]
                        if status==1:
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
        
def doRecognition(catList, curCatIdx, isRunning):
    isRunning.value = 1
    
    try:
        tempMap['skyName'] = 'tempPath'
        
    except Exception as e:
        print(e)
        tstr = traceback.format_exc()
        print(tstr)
    finally:
        isRunning.value = 0
        
class BatchImageDiff(object):
    
    def __init__(self):
        self.dataMgr = Manager()
        self.catList = self.dataMgr.list()
        self.catQueue = self.dataMgr.Queue()
        self.tmplMap = self.dataMgr.dict()
        self.cmbImgList = self.dataMgr.list()
        self.curCatIdx = 0
        self.tmplIdx = self.dataMgr.Value('i', -1)
        self.alignIdx = self.dataMgr.Value('i', -1)
        self.cmbIdx = self.dataMgr.Value('i', -1)
        
        self.catRunning = self.dataMgr.Value('i', 0)
        self.tmptRunning = self.dataMgr.Value('i', 0)
        self.alignRunning = self.dataMgr.Value('i', 0)
        self.cmbRunning = self.dataMgr.Value('i', 0)
        self.cmbCatRunning = self.dataMgr.Value('i', 0)
        self.diffRunning = self.dataMgr.Value('i', 0)
        self.recgRunning = self.dataMgr.Value('i', 0)
 
    def mainControl(self, camName):
        
        dateStr = datetime.strftime(datetime.utcnow(), "%Y%m%d")
        dataDest0 = "/data/gwac_diff_xy/data/%s"%(dateStr)
        logDest0 = "/data/gwac_diff_xy/log"
        if not os.path.exists(logDest0):
            os.system("mkdir -p %s"%(logDest0))
        if not os.path.exists(dataDest0):
            os.system("mkdir -p %s"%(dataDest0))
        
        toolPath = '/home/gwac/img_diff_xy/image_diff'
        tools = AstroTools(toolPath)
        
        imgDiff = BatchImageDiff(dataDest0, tools)
        tStr = "start diff..."
        tdiff.log.info(tStr)
        tdiff.sendMsg(tStr)
        
        loopNum = 1
        while True:
            
            curUtcDateTime = datetime.utcnow()
            tDateTime = datetime.utcnow()
            
            startDateTime = tDateTime.replace(hour=9, minute=0, second=0)  #9=17  1=9
            endDateTime = tDateTime.replace(hour=22, minute=0, second=0)  #22=6    8=16
            remainSeconds1 = (startDateTime - curUtcDateTime).total_seconds()
            remainSeconds2 = (endDateTime - curUtcDateTime).total_seconds()
            if not (remainSeconds1<0 and remainSeconds2>0):
                catIdx = loopNum%5
                if catIdx==1 and self.catRunning.value==0:  #cat
                    catJob = Process(target=srcExtract, args=(camName, self.catList, imgDiff, self.catRunning))
                    catJob.start()
                tmptIdx = loopNum%10
                if tmptIdx==0 and self.tmptRunning==0: #template
                    tmplJob = Process(target=newSkyTemplate, args=( self.tmptRunning))
                    tmplJob.start()
                alignIdx = loopNum%2
                if alignIdx==2 and self.alignRunning==0: #align
                    astmJob = Process(target=doAlign, args=( self.alignRunning))
                    astmJob.start()
                if self.cmbRunning==0: #combine5
                    astmJob = Process(target=doCombine, args=( self.cmbRunning))
                    astmJob.start()
                if self.cmbCatRunning==0: #cat of combine5
                    astmJob = Process(target=srcExtractCombine, args=( self.cmbCatRunning))
                    astmJob.start()
                if self.diffRunning==0: #diff
                    diffJob = Process(target=doDiff, args=( self.diffRunning))
                    diffJob.start()
                if self.recgRunning==0: #recognition
                    recgJob = Process(target=doRecognition, args=( self.recgRunning))
                    recgJob.start()
                    
                loopNum = loopNum + 1
                time.sleep(1)
                
            else:
                loopNum = 1
                time.sleep(10*60)
    
if __name__ == '__main__':
    lock=Lock()
    mgr = Manager()
    d = mgr.list()
    jobs = [ Process(target=worker, args=(d, i, i*2, lock))
             for i in range(10)
             ]
    for j in jobs:
        j.start()
    for j in jobs:
        j.join()
    print ('Results:' )
    #for key, value in enumerate(dict(d)):
    #    print("%s=%s" % (key, value))
    for sky in d:
        print(sky)