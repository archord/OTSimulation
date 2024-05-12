# -*- coding: utf-8 -*-
import os
import requests
import traceback
from datetime import datetime

def crossTaskCreate(taskName, crossMethod, serverIP):
    
    mergedR = 0.0167
    mergedMag = 20
    cvsR = 0.0167
    cvsMag = 20
    rc3R = 0.03333
    rc3MaxMag = 20
    rc3MinMag = -20
    minorPlanetR = 0.05
    minorPlanetMag = 16
    ot2HisR = 0.01
    ot2HisMag = 20
    usnoR1 = 0.016667
    usnoMag1 = 15.5
    usnoR2 = 0.041667
    usnoMag2 = 8

    needStarMatch = 0 # 0代表不与星表（usno等）匹配，1代表匹配
    comment = "object description info: " #描述信息，最长4k
    taskType = "SVOM-Eclairs"  #任务类型：SVOM-Eclairs，SVOM-GRM ， SVOM-subthreshold ，Swift-BAT 
    detector = "GWAC" # GWAC, F60A，F60B，F50A，F30A
     
    try:
        turl = "http://%s:8080/crosstask/crossTaskCreate.action"%(serverIP)
        
        values = {'taskName': taskName, 
                  'mergedR': mergedR, 
                  'mergedMag': mergedMag, 
                  'cvsR': cvsR, 
                  'cvsMag': cvsMag, 
                  'rc3R': rc3R, 
                  'rc3MaxMag': rc3MaxMag, 
                  'rc3MinMag': rc3MinMag, 
                  'minorPlanetR': minorPlanetR, 
                  'minorPlanetMag': minorPlanetMag, 
                  'ot2HisR': ot2HisR, 
                  'ot2HisMag': ot2HisMag, 
                  'usnoR1': usnoR1, 
                  'usnoMag1': usnoMag1, 
                  'usnoR2': usnoR2, 
                  'usnoMag2': usnoMag2, 
                  'crossMethod': crossMethod, 
                  'needStarMatch': needStarMatch, 
                  'comment': comment, 
                  'taskType': taskType, 
                  'detector': detector}
        
        msgSession = requests.Session()
        r = msgSession.post(turl, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)
        
def crossTaskUpload(taskName, ftype, path, fnames, serverIP):
    
    try:
        turl = "http://%s:8080/crosstask/crossTaskUpload.action"%(serverIP)
        
        sendTime = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
        values = {'taskName': taskName, 
                  'fileType': ftype, 
                  'sendTime': sendTime}
        files = []
        
        for tfname in fnames:
            tpath = "%s/%s"%(path, tfname)
            files.append(('fileUpload', (tfname,  open(tpath,'rb'), 'text/plain')))
        
        msgSession = requests.Session()
        r = msgSession.post(turl, files=files, data=values)
        
        print(r.text)
    except Exception as e:
        tstr = traceback.format_exc()
        print(tstr)

def crossTaskUploadTest():
    
    #任务管理服务器的IP
    serverIP = '10.36.1.77'
    #创建的任务名称
    taskName = '20190425_G21_combine25_1'
    #交叉匹配类型：
    #1，一个位置只要检测到一次，就任务是一个OT，后面相同位置的目标追加到观测记录
    #2，对同一个位置至少需要再连续的N（5）帧中出现两次
    crossMethod = '2' 
    
    #任务创建/注册
    crossTaskCreate(taskName, crossMethod, serverIP)
     
    ''' '''
    ftype = 'crossOTList'
    path = 'data'
    fnames = ['G021_mon_objt_190421T11580477.cat']
    #任务文件上传
    crossTaskUpload(taskName, ftype, path, fnames, serverIP)
    crossTaskUpload(taskName, ftype, path, fnames, serverIP)
    
    ftype = 'crossOTStamp'
    path = 'data'
    fnames = ['G024_tom_objt_190413T19200211_2_c_c_00005.jpg']
    crossTaskUpload(taskName, ftype, path, fnames, serverIP)
    
def crossTaskUploadTest2():
    
    #任务管理服务器的IP
    serverIP = '127.0.0.1'
    #创建的任务名称
    taskName = '230916_G042_24960425_C005'
    #交叉匹配类型：
    #1，一个位置只要检测到一次，就任务是一个OT，后面相同位置的目标追加到观测记录
    #2，对同一个位置至少需要再连续的N（5）帧中出现两次
    crossMethod = '1' 
    
    #任务创建/注册
    crossTaskCreate(taskName, crossMethod, serverIP)
     
    otListDir = "gwacInSvomRealTime/upload2Server/crossTaskData/230916_G042_24960425_C005/crossOTList"
    otStampDir = "gwacInSvomRealTime/upload2Server/crossTaskData/230916_G042_24960425_C005/crossOTStamp"

    ''' '''
    ftype = 'crossOTList'
    fnames = [] #'G021_mon_objt_190421T11580477.cat'
    otlistFiles = os.listdir(otListDir)
    for otlistFile in otlistFiles:
        if otlistFile.endswith('.cat'):
            fnames.append(otlistFile)
    #任务文件上传
    crossTaskUpload(taskName, ftype, otListDir, fnames, serverIP)
    
    ftype = 'crossOTStamp'
    imgs = [] #'G024_tom_objt_190413T19200211_2_c_c_00005.jpg'
    otStampImgs = os.listdir(otStampDir)
    for otStampImg in otStampImgs:
        if otStampImg.endswith('.jpg'):
            imgs.append(otStampImg)
    crossTaskUpload(taskName, ftype, otStampDir, imgs, serverIP)
        
if __name__ == "__main__":
    
    crossTaskUploadTest2()