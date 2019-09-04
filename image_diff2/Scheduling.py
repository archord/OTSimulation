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
                    isSuccess, skyName, starNum, fwhmMean, bgMean = imgDiff.getCat(srcDir, timgName)
                    if isSuccess:
                        catList.append((isSuccess, ffId, timgName, starNum, skyName, fwhmMean, bgMean, curSkyId))
                    endtime = datetime.now()
                    runTime = (endtime - starttime).seconds
                    imgDiff.log.info("totalTime %d seconds, sky:%d, ffNum:%d, %s"%(runTime, curSkyId, ffNumber, timgName))
                else:
                    imgDiff.log.error("getCat: %s not exist"%(tpath))

        except Exception as e:
            tstr = traceback.format_exc()
            imgDiff.log.error(tstr)

    isRunning.value = 0
    
def newSkyTemplate(camName, catList, tIdx, imgDiff, isRunning):
    
    isRunning.value = 1
    makeTmpl = False
    try:
        catNum = len(catList)
        if catNum>1:
            lastIdx = tIdx.value
            if catNum-1>lastIdx:
                for i in range(lastIdx+1, catNum):
                    tcatParm = catList[i]
                    skyId = tcatParm[7]
                    skyName = tcatParm[4]
                    if i==0:
                        query = QueryData()
                        tmpls = query.getTmplList(camName, skyId)
                        makeTmpl = True
                    else:
                        skyName0 = catList[i-1][4]
                        if skyName0!=skyName:
                            tmpls = query.getTmplList(camName, skyId)
                            makeTmpl = True
                    if makeTmpl:
                        if len(tmpls)>0:
                            print('down template')
                        else:
                            print('make new template')
        
    except Exception as e:
        print(e)
        tstr = traceback.format_exc()
        print(tstr)
    finally:
        isRunning.value = 0
    
def doAlign(catList, curCatIdx, isRunning):
    isRunning.value = 1
    
    try:
        tempMap['skyName'] = 'tempPath'
        
    except Exception as e:
        print(e)
        tstr = traceback.format_exc()
        print(tstr)
    finally:
        isRunning.value = 0
        
def doCombine(catList, curCatIdx, isRunning):
    isRunning.value = 1
    
    try:
        tempMap['skyName'] = 'tempPath'
        
    except Exception as e:
        print(e)
        tstr = traceback.format_exc()
        print(tstr)
    finally:
        isRunning.value = 0

def doDiff(catList, curCatIdx, isRunning):
    isRunning.value = 1
    
    try:
        tempMap['skyName'] = 'tempPath'
        
    except Exception as e:
        print(e)
        tstr = traceback.format_exc()
        print(tstr)
    finally:
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
        self.tempMap = self.dataMgr.dict()
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
                if self.tmptRunning==0: #template
                    tmplJob = Process(target=newSkyTemplate, args=( self.tmptRunning))
                    tmplJob.start()
                if self.alignRunning==0: #align
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