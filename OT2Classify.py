# -*- coding: utf-8 -*-
#12像素，FOT观测假OT2，TOT小辛图像, 减背景和不减背景
from astropy.io import fits
import numpy as np
import math
import os
import shutil
from datetime import datetime
from keras.models import load_model
from getOTImgsAll2 import OTRecord
from DataPreprocess2 import getImgStamp
from datetime import datetime, timedelta
import time
import sys
    
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
                print("get %d ot2"%(otNum))
                
                if otNum > 0:
                    timgs = getImgStamp(timgs, size=imgSize, padding = 0, transMethod='none')
                    preY = model.predict(timgs, batch_size=128)
                    #print(timgs.shape)
                    #print(preY.shape)
                    
                    for i in range(props.shape[0]):
    
                        otName = props[i][0]
                        if preY[i][1]>=0.5:
                            prb = 1
                        else:
                            prb = 0
                        mr.updateOT2LookBackCNN(otName, prb)
                time.sleep(60)
            else:
                time.sleep(10*60)
                print("sleep 600 seconds")
            sys.stdout.flush()
        except Exception as e:
            print(str(e))
            

#nohup python OT2Classify.py >> OT2Classify.log &
if __name__ == "__main__":
    
    realDataClassify()



