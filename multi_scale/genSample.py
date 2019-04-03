# -*- coding: utf-8 -*-
import numpy as np
import math
import os
import traceback
from random import random

def imgTransform(data1, data2, data3, transMethod='none'):
    
    data1[data1<0] = 0
    data2[data2<0] = 0
    data3[data3<0] = 0
    tmax1 = np.max(data1)
    tmax2 = np.max(data2)
    tmax3 = np.max(data3)
    tmax = np.max([tmax1, tmax2,tmax3])

    tminMaxValue = 50
    if transMethod == 'eachMax':
        if tmax1>tminMaxValue and tmax2>tminMaxValue and tmax3>tminMaxValue:
            data1 = data1*255.0/tmax1
            data2 = data2*255.0/tmax2
            data3 = data3*255.0/tmax3
        elif tmax1>tminMaxValue and tmax2<=tminMaxValue and tmax3>tminMaxValue:
            data1 = data1*255.0/tmax1
            data2 = data2
            data3 = data3*255.0/tmax3
        else:
            data1, data2, data3 = np.array([]), np.array([]), np.array([])
    elif transMethod == 'unionMax':
        if tmax<tminMaxValue:
            data1, data2, data3 = np.array([]), np.array([]), np.array([])
        else:
            data1 = data1*255.0/tmax
            data2 = data2*255.0/tmax
            data3 = data3*255.0/tmax
    
    if transMethod == 'eachMax' or transMethod == 'unionMax' or transMethod == 'zscale':
        data1[data1>255] = 255
        data2[data2>255] = 255
        data3[data3>255] = 255
        
        data1 = data1.astype(np.uint8)
        data2 = data2.astype(np.uint8)
        data3 = data3.astype(np.uint8)
    elif transMethod == 'none': #preMethod4
        data1[data1>65535] = 65535
        data2[data2>65535] = 65535
        data3[data3>65535] = 65535
        data1 = data1.astype(np.uint16)
        data2 = data2.astype(np.uint16)
        data3 = data3.astype(np.uint16)
    
    return data1, data2, data3
    
def getImgStamp(imgArray, size=12, padding = 1, transMethod='none'):
    
    rst = np.array([])
    if len(imgArray.shape)==4 and imgArray.shape[0]>0:
        
        imgSize = imgArray[0][0][0].shape[0]
        ctrIdx = math.ceil(imgSize/2.0) - 1
        halfWid = math.floor(size/2.0)
        minIdx = ctrIdx - halfWid - padding
        maxIdx = ctrIdx + halfWid - padding
        
        rstImgs = []
        for timgs in imgArray:
            img1 = timgs[0][minIdx:maxIdx,minIdx:maxIdx]
            img2 = timgs[1][minIdx:maxIdx,minIdx:maxIdx]
            img3 = timgs[2][minIdx:maxIdx,minIdx:maxIdx]
            
            img1, img2, img3 = imgTransform(img1, img2, img3, transMethod)
            if img1.shape[0]>0 and img2.shape[0]>0 and img3.shape[0]>0:
                rstImgs.append([img1,img2,img3])
        rst = np.array(rstImgs)
    return rst

def getData1(spath, dpath, saveName, total=10000, imgSize=64, transMethod='none'):
 
    imgs = np.array([])
    s2ns = np.array([])
    
    tdirs = os.listdir(spath)
    for i, fname in enumerate(tdirs):
        try:
            tpath21 = "%s/%s"%(spath, fname)
            print("%d:%s"%(i,tpath21))
            fdata1 = np.load(tpath21)
            fotImg = fdata1['imgs']
            fprops = fdata1['parms']
                            
            fotImg = getImgStamp(fotImg, size=imgSize, padding = 1, transMethod='none')
            #fs2n = np.zeros(fotImg.shape[0])
            fs2n = 1.087/fprops[:,12].astype(np.float)
            
            if imgs.shape[0]==0:
                imgs = fotImg
                s2ns = fs2n
            else:
                imgs = np.concatenate((imgs, fotImg), axis=0)
                s2ns = np.concatenate((s2ns, fs2n), axis=0)
            if imgs.shape[0]>total:
                break
        except Exception as e:
            tstr = traceback.format_exc()
            print(tstr)
            
    print("%s %d"%(saveName,imgs.shape[0]))
    timgbinPath = '%s/%s_temp.npz'%(dpath, saveName)
    np.savez_compressed(timgbinPath, imgs=imgs, s2ns=s2ns)
    return timgbinPath
    
def getData2(spath, dpath, saveName, total=10000, imgSize=64, transMethod='none'):
        
    totImgs = np.array([])
    ts2ns = np.array([])
    
    totNum = 0
    tdirs = os.listdir(spath)
    tdirs.sort()
    for i, fname in enumerate(tdirs):
        try:
            tpath1 = "%s/%s"%(spath, fname)
            print("%d:%s"%(i,tpath1))
            tdata1 = np.load(tpath1)
            
            totImg = tdata1['tot']
            ts2n = tdata1['ts2n']
            totImg = getImgStamp(totImg, size=imgSize, padding = 1, transMethod='none')
            
            if totImgs.shape[0]==0:
                totImgs = totImg
                ts2ns = ts2n
            else:
                totImgs = np.concatenate((totImgs, totImg), axis=0)
                ts2ns = np.concatenate((ts2ns, ts2n), axis=0)
            
            totNum = totNum + totImg.shape[0]
            if totNum >= total:
                break
            #break
        except Exception as e:
            tstr = traceback.format_exc()
            print(tstr)
            
    print("totImgs1 %d"%(totImgs.shape[0]))
    timgbinPath = '%s/%s_temp.npz'%(dpath, saveName)
    np.savez_compressed(timgbinPath, imgs=totImgs, s2ns=ts2ns)
    return timgbinPath
        
        
def getAll():
    
    #20190116bad  20190116tot  badimg2  fotimg  rest_data_20190120
    fotpath = "fotimg"
    totpath1 = "rest_data_20190120"
    totpath2 = "20190116tot"
    badpath1 = "20190116bad"
    badpath2 = "badimg2"
    
    dpath = 'allsample'
    fp = getData1(fotpath, dpath, 'fotimg', total=200000, imgSize=64, transMethod='none')
    tp2 = getData1(totpath2, dpath, 'totimg2', total=60000, imgSize=64, transMethod='none')
    bp1 = getData1(badpath1, dpath, 'badimg1', total=20000, imgSize=64, transMethod='none')
    bp2 = getData1(badpath2, dpath, 'badimg2', total=200000, imgSize=64, transMethod='none')
    tp1 = getData2(totpath1, dpath, 'totimg1', total=500000, imgSize=64, transMethod='none')
    
    fdata = np.load(fp)
    tdata2 = np.load(tp2)
    bdata1 = np.load(bp1)
    bdata2 = np.load(bp2)
    tdata1 = np.load(tp1)
    
    fotImgs = np.concatenate((fdata['imgs'], tdata2['imgs'], bdata1['imgs'],bdata2['imgs']), axis=0)
    fs2ns = np.concatenate((fdata['s2ns'], tdata2['s2ns'], bdata1['s2ns'],bdata2['s2ns']), axis=0)
    totImgs = tdata1['imgs']
    ts2ns = tdata1['s2ns']
    
    totNum = totImgs.shape[0]
    fotNum = fotImgs.shape[0]
    if totNum>fotNum:
        totImgs = totImgs[0:fotNum]
        ts2ns = ts2ns[0:fotNum]
    elif totNum<fotNum:
        fotImgs = fotImgs[0:totNum]
        fs2ns = fs2ns[0:totNum]

    totSize = totImgs.shape[0]
    fotSize = fotImgs.shape[0]
    totLabel = np.ones(totSize)
    fotLabel = np.zeros(fotSize)
    X = np.concatenate((totImgs, fotImgs), axis=0)
    s2n = np.concatenate((ts2ns, fs2ns), axis=0)
    y = np.concatenate((totLabel, fotLabel), axis=0)
    Y = np.array([np.logical_not(y), y]).transpose()
        
    XY = []
    for i in range(Y.shape[0]):
        XY.append((X[i],Y[i],s2n[i]))
    XY = np.array(XY)
    np.random.shuffle(XY)
    
    X = []
    Y = []
    s2n = []
    for i in range(XY.shape[0]):
        X.append(XY[i][0])
        Y.append(XY[i][1])
        s2n.append(XY[i][2])
    X = np.array(X)
    Y = np.array(Y)
    s2n = np.array(s2n)
    print(X.shape)
    
    timgbinPath = '%s/AllSample.npz'%(dpath)
    np.savez_compressed(timgbinPath, X=X, Y=Y, s2n=s2n)
    print("save bin fiel to %s"%(timgbinPath))
    
if __name__ == "__main__":
    
    spath='/home/gwac/gwac_ot'
    
    getAll()
    