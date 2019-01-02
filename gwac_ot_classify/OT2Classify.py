from astropy.io import fits
import numpy as np
import math
import os
import shutil
import scipy.ndimage
from datetime import datetime
from keras.models import load_model
from DataPreprocess import getImgStamp
from datetime import datetime, timedelta
import time
import sys
from PIL import Image
from gwac_util import zscale_image
import matplotlib.pyplot as plt

def showImage(imgs, props, predY, label, showNum=10):
    
    for i in range(imgs.shape[0]):
        
        #if i>=showNum:
        #    break
        
        s2n = 1.087/props[i,12].astype(np.float)
        #print(props[i])
        X = props[i][0]
        Y = props[i][1]
        if math.fabs(Y-2616.9944)>5:
            continue
        ELONGATION = props[i][5]
        ELLIPTICITY = props[i][6]
        print("ELONGATION=%.2f,ELLIPTICITY=%.2f,X=%.2f,Y=%.2f"%(ELONGATION,ELLIPTICITY,X, Y))
        
        objWidz = zscale_image(imgs[i][0])
        tmpWidz = zscale_image(imgs[i][1])
        resiWidz = zscale_image(imgs[i][2])
        if objWidz.shape[0] == 0:
            objWidz = imgs[i][0]
        if tmpWidz.shape[0] == 0:
            tmpWidz = imgs[i][1]
        if resiWidz.shape[0] == 0:
            resiWidz = imgs[i][2]
        plt.clf()
        fig, axes = plt.subplots(1, 3, figsize=(3, 3))
        axes.flat[0].imshow(objWidz, interpolation = "nearest", cmap='gray')
        axes.flat[1].imshow(tmpWidz, interpolation = "nearest", cmap='gray')
        axes.flat[2].imshow(resiWidz, interpolation = "nearest", cmap='gray')
        axes.flat[1].set_title("predicted pbb=%.2f, label=%s, s2n=%.2f\n"%(predY[i][1],label,s2n))
        plt.show()
    
def realDataTest():
    
    imgSize = 8
    pbb_threshold = 0.5
    workPath = "//home/xy/Downloads/myresource/deep_data2/simot/train_20190102"
    model = load_model("%s/model_128_5_RealFOT_8.h5"%(workPath))
    
    dataPath = '/home/xy/Downloads/myresource/deep_data2/simot/G181208_C03490'
    
    flist = os.listdir(dataPath)
    flist.sort()
    
    for tfilename in flist:
        
        #G034_mon_objt_181208T10463819
        #G044_mon_objt_181208T10391696
        #G024_mon_objt_181206T12154991_otimg
        if tfilename.find('G044_mon_objt_181208T10391696')==-1:
            continue
        print(tfilename)
        
        tpath = "%s/%s"%(dataPath, tfilename)
        tdata1 = np.load(tpath)
        timg32s = tdata1['fot']
        props = tdata1['parms']
        #fs2n = 1.087/props[:,12].astype(np.float)
        
        timgs = getImgStamp(timg32s, size=imgSize, padding = 0, transMethod='none')
        print(timgs.shape)
        preY = model.predict(timgs, batch_size=128)
        
        trueIdx = preY[:, 1] > pbb_threshold
        falseIdx = preY[:, 1] <= pbb_threshold
        
        trueNum = np.array(trueIdx, dtype = "int").sum()
        falseNum = np.array(falseIdx, dtype = "int").sum()
        
        print("total %d, true %d, false %d"%(timgs.shape[0], trueNum, falseNum))
        
        trueImgs = timg32s[trueIdx]
        trueProps = props[trueIdx]
        truePreYs = preY[trueIdx]
        
        falseImgs = timg32s[falseIdx]
        falseProps = props[falseIdx]
        falsePreYs = preY[falseIdx]
        
        print("\n\n***********************")
        print("%d images classified as False"%(trueNum))
        showImage(trueImgs, trueProps, truePreYs, 'OT', showNum=1000)
        
        print("\n\n***********************")
        print("%d images classified as False"%(falseNum))
        showImage(falseImgs, falseProps, falsePreYs, 'FOT', showNum=5000)
        
        
  

#nohup python OT2Classify.py >> OT2Classify.log &
if __name__ == "__main__":
    
    realDataTest()


