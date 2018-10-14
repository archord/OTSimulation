# -*- coding: utf-8 -*-
#12像素，FOT观测假OT2，TOT小辛图像, 减背景和不减背景
from astropy.io import fits
import numpy as np
import math
import os
import shutil
import scipy.ndimage
from datetime import datetime
from keras.models import load_model
from getOTImgsAll2 import OTRecord
from DataPreprocess2 import getImgStamp
from datetime import datetime, timedelta
import time
import sys
from PIL import Image
    
def realDataTest():
    
    imgSize = 8
    pbb_threshold = 0.5
    workPath = "/data/work/program/ot2classify"
    model = load_model("%s/model_128_5_RealFOT_8.h5"%(workPath))
    
    mr = OTRecord()
    timgs, props = mr.getOTImgs()
    mr.closeDb()
        
    timgs = getImgStamp(timgs, size=imgSize, padding = 0, transMethod='none')
    print(timgs.shape)
    preY = model.predict(timgs, batch_size=128)
    
    tmpIdx = props[:,5]=='2'
    tot2Idx = props[:,4]=='1'
    otherIdx = props[:,4]!='1'
    
    mpImgs = timgs[tmpIdx]
    ot2Imgs = timgs[tot2Idx]
    otherImgs = timgs[otherIdx]
    
    trueMP = np.array((preY[tmpIdx, 1] > pbb_threshold), dtype = "int").sum()
    trueOT2 = np.array((preY[tot2Idx, 1] > pbb_threshold), dtype = "int").sum()
    trueOther = np.array((preY[otherIdx, 1] > pbb_threshold), dtype = "int").sum()
    
    print("total minor planet %d, classify as true %d"%(mpImgs.shape[0], trueMP))
    print("look back TOT %d, classify as true %d"%(ot2Imgs.shape[0], trueOT2))
    print("look back FOT %d, classify as true %d"%(otherImgs.shape[0], trueOther))

def saveOT2View(ot2Name, ot2Imgs, innerSpace=1, scale=10):
    
    dateStr = ot2Name[1:7]
    rootPath = '/data/gwac_data/ot2lbcnn/%s'%(dateStr)
    if not os.path.exists(rootPath):
        os.makedirs(rootPath)
    
    objImgz, refImgz, diffImgz = ot2Imgs[0], ot2Imgs[1], ot2Imgs[2]
    xspace = np.ones((objImgz.shape[0],innerSpace), np.uint8)*255
    conImg = np.concatenate((objImgz, xspace, refImgz, xspace, diffImgz), axis=1)
    conImg = scipy.ndimage.zoom(conImg, scale, order=0)
    
    savePath = "%s/%s.jpg"%(rootPath,ot2Name)
    Image.fromarray(conImg).save(savePath)
    
def hisDataClassify():
    
    imgSize = 8
    workPath = "/data/work/program/ot2classify"
    model = load_model("%s/model_128_5_RealFOT_8.h5"%(workPath))
    

    try:

        dateStr = '181011'
        dpath = "/data/work/ot2_img_collection_%s"%(dateStr)
        mr = OTRecord()
        timgs, props = mr.getHisOTImgs(dpath, dateStr)
        otNum = timgs.shape[0]
        print("get %d ot2"%(otNum))
        
        if otNum > 0:
            timgs2 = getImgStamp(timgs, size=imgSize, padding = 0, transMethod='none')
            preY = model.predict(timgs2, batch_size=128)
            print(timgs2.shape)
            print(preY.shape)
            
            tzimgs = getImgStamp(timgs, size=imgSize, padding = 0, transMethod='zscale')
            print(tzimgs.shape)
            for i in range(props.shape[0]): #timgs, props, timgs2, tzimgs数量有可能不一样
    
                otName = props[i][0]
                '''
                if preY[i][1]>=0.5:
                    prb = 1
                else:
                    prb = 0
                mr.updateOT2LookBackCNN(otName, prb)
                '''
                saveOT2View(otName, tzimgs[i])


    except Exception as e:
        print(str(e))
            
def realDataClassify():
    
    imgSize = 8
    workPath = "/data/work/program/ot2classify"
    model = load_model("%s/model_128_5_RealFOT_8.h5"%(workPath))
    
    mr = OTRecord()

    while True:
        try:
            curDateTime = datetime.now()
            tDateTime = datetime.now()
            startDateTime1 = tDateTime.replace(hour=17, minute=0, second=0)
            endDateTime1 = tDateTime.replace(hour=23, minute=59, second=59)
            startDateTime2 = tDateTime.replace(hour=0, minute=0, second=0)
            endDateTime2 = tDateTime.replace(hour=8, minute=0, second=0)
            
            remainSeconds11 = (startDateTime1 - curDateTime).total_seconds()
            remainSeconds12 = (endDateTime1 - curDateTime).total_seconds()
            remainSeconds21 = (startDateTime2 - curDateTime).total_seconds()
            remainSeconds22 = (endDateTime2 - curDateTime).total_seconds()
            if (remainSeconds11<0 and remainSeconds12>0) or (remainSeconds21<0 and remainSeconds22>0):

                timgs, props = mr.getOTImgs()
                otNum = timgs.shape[0]
                #print("get %d ot2"%(otNum))
                
                if otNum > 0:
                    timgs2 = getImgStamp(timgs, size=imgSize, padding = 0, transMethod='none')
                    preY = model.predict(timgs2, batch_size=128)
                    #print(timgs2.shape)
                    #print(preY.shape)
                    
                    tzimgs = getImgStamp(timgs, size=imgSize, padding = 0, transMethod='zscale')
                    for i in range(props.shape[0]): #timgs, props, timgs2, tzimgs数量有可能不一样
    
                        otName = props[i][0]
                        if preY[i][1]>=0.5:
                            prb = 1
                        else:
                            prb = 0
                        mr.updateOT2LookBackCNN(otName, prb)
                        
                        saveOT2View(otName, tzimgs[i])
                time.sleep(60)
            else:
                time.sleep(10*60)
                #print("sleep 600 seconds")
            sys.stdout.flush()
        except Exception as e:
            print(str(e))
            

#nohup python OT2Classify.py >> OT2Classify.log &
if __name__ == "__main__":
    
    realDataClassify()
    #hisDataClassify()


