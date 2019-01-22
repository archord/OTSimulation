# -*- coding: utf-8 -*-
from astropy.io import fits
import numpy as np
import math
import os
import shutil
from datetime import datetime
import matplotlib.pyplot as plt
from gwac_util import zscale_image
import traceback
import scipy.ndimage

'''
preMethod: 
1, eachMax: obj tmp and resi transform to 255 by each maxValue(three max value)
2, unionMax: obj tmp and resi transform to 255 by union maxValue(one max value)
3, zscale: obj tmp and resi transform to 255 by zscale 
4, none: donot execuate any operation
'''
def imgTransform(data1, data2, data3, transMethod='none', zoomSize=0.5):
    
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
    elif transMethod == 'zscale':
        tdata1 = zscale_image(data1)
        tdata2 = zscale_image(data2)
        tdata3 = zscale_image(data3)
        if tdata1.shape[0]==0:
            tmin = np.min(data1)
            tmax = np.max(data1)
            tdata1=(((data1-tmin)/(tmax-tmin))*255).astype(np.uint8)
        if tdata2.shape[0]==0:
            tmin = np.min(data2)
            tmax = np.max(data2)
            tdata2=(((data2-tmin)/(tmax-tmin))*255).astype(np.uint8)
        if tdata3.shape[0]==0:
            tmin = np.min(data3)
            tmax = np.max(data3)
            tdata3=(((data3-tmin)/(tmax-tmin))*255).astype(np.uint8)
        data1 = tdata1
        data2 = tdata2
        data3 = tdata3
    elif transMethod == 'zoom':
        data1 = scipy.ndimage.zoom(data1, zoomSize, order=0)
        data2 = scipy.ndimage.zoom(data2, zoomSize, order=0)
        data3 = scipy.ndimage.zoom(data3, zoomSize, order=0)
    
    if transMethod == 'eachMax' or transMethod == 'unionMax' or transMethod == 'zscale':
        data1[data1>255] = 255
        data2[data2>255] = 255
        data3[data3>255] = 255
        
        data1 = data1.astype(np.uint8)
        data2 = data2.astype(np.uint8)
        data3 = data3.astype(np.uint8)
    elif transMethod == 'none' or transMethod == 'zoom': #preMethod4
        data1[data1>65535] = 65535
        data2[data2>65535] = 65535
        data3[data3>65535] = 65535
        data1 = data1.astype(np.uint16)
        data2 = data2.astype(np.uint16)
        data3 = data3.astype(np.uint16)
    
    return data1, data2, data3
    
def getImgStamp(imgArray, size=(64,8), padding = 1, transMethod=('zoom', 'none')):
    
    rst1 = np.array([])
    rst2 = np.array([])
    if len(imgArray.shape)==4 and imgArray.shape[0]>0:
        
        imgSize = imgArray[0][0][0].shape[0]
        ctrIdx = math.ceil(imgSize/2.0) - 1
        halfWid1 = math.floor(size[0]/2.0)
        minIdx1 = ctrIdx - halfWid1 - padding
        maxIdx1 = ctrIdx + halfWid1 - padding
        halfWid2 = math.floor(size[1]/2.0)
        minIdx2 = ctrIdx - halfWid2 - padding
        maxIdx2 = ctrIdx + halfWid2 - padding
        
        rstImgs1 = []
        rstImgs2 = []
        for timgs in imgArray:
            img1 = timgs[0][minIdx1:maxIdx1,minIdx1:maxIdx1]
            img2 = timgs[1][minIdx1:maxIdx1,minIdx1:maxIdx1]
            img3 = timgs[2][minIdx1:maxIdx1,minIdx1:maxIdx1]
            
            img1, img2, img3 = imgTransform(img1, img2, img3, transMethod[0], zoomSize=0.5)
            if img1.shape[0]>0 and img2.shape[0]>0 and img3.shape[0]>0:
                rstImgs1.append([img1,img2,img3])
                
            img1 = timgs[0][minIdx2:maxIdx2,minIdx2:maxIdx2]
            img2 = timgs[1][minIdx2:maxIdx2,minIdx2:maxIdx2]
            img3 = timgs[2][minIdx2:maxIdx2,minIdx2:maxIdx2]
            
            img1, img2, img3 = imgTransform(img1, img2, img3, transMethod[1])
            if img1.shape[0]>0 and img2.shape[0]>0 and img3.shape[0]>0:
                rstImgs2.append([img1,img2,img3])
                
        rst1 = np.array(rstImgs1)
        rst2 = np.array(rstImgs2)
    return rst1, rst2
    
def getData(totPath, fotPath, destPath, tNamePart, imgSize=(64,8), transMethod=('zoom', 'none')):
    
    timgbinPath = '%s/SIM_TOT_REAL_FOT_bin_%s_%s.npz'%(destPath, transMethod, tNamePart)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X64 = timgbin['X64']
        X8 = timgbin['X8']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
    else:
                
        #realFotPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart"
        tdirs = os.listdir(fotPath)
        tdirs.sort()
        
        badImgfiles = []
        fotImgfiles = []
        totImgfiles = []
        for tfile in tdirs:
            if tfile.find('bad')>-1:
                badImgfiles.append(tfile)
            elif tfile.find('fot')>-1:
                fotImgfiles.append(tfile)
            elif tfile.find('tot')>-1:
                totImgfiles.append(tfile)
        
        fotImgs64 = np.array([])
        fotImgs8= np.array([])
        fs2ns = np.array([])
        for i, fname in enumerate(fotImgfiles):
            #if fname[:3]=='fot':
            try:
                tpath21 = "%s/%s"%(fotPath, fname)
                print("%d:%s"%(i,tpath21))
                fdata1 = np.load(tpath21)
                fotImg = fdata1['imgs']
                fprops = fdata1['parms']
                
                if fotImg.shape[0]>600:
                    continue
                
                fotImg64, fotImg8 = getImgStamp(fotImg, size=imgSize, padding = 1, transMethod=('zoom', 'none'))
                #fs2n = np.zeros(fotImg.shape[0])
                fs2n = 1.087/fprops[:,12].astype(np.float)
                
                if fotImgs64.shape[0]==0:
                    fotImgs64 = fotImg64
                    fotImgs8 = fotImg8
                    fs2ns = fs2n
                else:
                    fotImgs64 = np.concatenate((fotImgs64, fotImg64), axis=0)
                    fotImgs8 = np.concatenate((fotImgs8, fotImg8), axis=0)
                    fs2ns = np.concatenate((fs2ns, fs2n), axis=0)
                if i>50:
                    break
                
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
        
        
        badImgs64 = np.array([])
        badImgs8 = np.array([])
        bads2ns = np.array([])
        for i, fname in enumerate(badImgfiles):
            #if fname[:3]=='fot':
            try:
                tpath21 = "%s/%s"%(fotPath, fname)
                print("%d:%s"%(i,tpath21))
                fdata1 = np.load(tpath21)
                fotImg = fdata1['imgs']
                fprops = fdata1['parms']
                
                if fotImg.shape[0]>600:
                    continue
                
                fotImg64, fotImg8 = getImgStamp(fotImg, size=imgSize, padding = 1, transMethod=('zoom', 'none'))
                fs2n = np.zeros(fotImg.shape[0])
                #fs2n = 1.087/fprops[:,12].astype(np.float)
                
                if badImgs64.shape[0]==0:
                    badImgs64 = fotImg64
                    badImgs8 = fotImg8
                    bads2ns = fs2n
                else:
                    badImgs64 = np.concatenate((badImgs64, fotImg64), axis=0)
                    badImgs8 = np.concatenate((badImgs8, fotImg8), axis=0)
                    bads2ns = np.concatenate((bads2ns, fs2n), axis=0)
                if i>50:
                    break
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
        
        print("fotSize %d"%(fotImgs64.shape[0]))
        print("badSize %d"%(badImgs64.shape[0]))
        
        fotImgs64 = np.concatenate((fotImgs64, badImgs64), axis=0)
        fotImgs8 = np.concatenate((fotImgs8, badImgs8), axis=0)
        fs2ns = np.concatenate((fs2ns, bads2ns), axis=0)
        print("fotImgs %d"%(fotImgs64.shape[0]))
        print("fs2ns %d"%(fs2ns.shape[0]))
        
        totImgs64 = np.array([])
        totImgs8 = np.array([])
        ts2ns = np.array([])
        
        totNum = 0
        tdirs = os.listdir(totPath)
        tdirs.sort()
        for fname in tdirs:
            tpath1 = "%s/%s"%(totPath, fname)
            #print(tpath1)
            tdata1 = np.load(tpath1)
            
            totImg = tdata1['tot']
            ts2n = tdata1['ts2n']
            totImg64, totImg8 = getImgStamp(totImg, size=imgSize, padding = 1, transMethod=('zoom', 'none'))
            
            if totImgs64.shape[0]==0:
                totImgs64 = totImg64
                totImgs8 = totImg8
                ts2ns = ts2n
            else:
                totImgs64 = np.concatenate((totImgs64, totImg64), axis=0)
                totImgs8 = np.concatenate((totImgs8, totImg8), axis=0)
                ts2ns = np.concatenate((ts2ns, ts2n), axis=0)
            
            totNum = totNum + totImg.shape[0]
            if totNum >= fotImgs64.shape[0]:
                break
            #break
                
        print("totSize %d"%(totImgs64.shape[0]))
        
        totNum = totImgs64.shape[0]
        fotNum = fotImgs64.shape[0]
        if totNum>fotNum:
            totImgs64 = totImgs64[0:fotNum]
            totImgs8 = totImgs8[0:fotNum]
            ts2ns = ts2ns[0:fotNum]
        elif totNum<fotNum:
            fotImgs64 = fotImgs64[0:totNum]
            fotImgs8 = fotImgs8[0:totNum]
            fs2ns = fs2ns[0:totNum]

        totSize = totImgs64.shape[0]
        fotSize = fotImgs64.shape[0]
        totLabel = np.ones(totSize)
        fotLabel = np.zeros(fotSize)
        X64 = np.concatenate((totImgs64, fotImgs64), axis=0)
        X8 = np.concatenate((totImgs8, fotImgs8), axis=0)
        s2n = np.concatenate((ts2ns, fs2ns), axis=0)
        y = np.concatenate((totLabel, fotLabel), axis=0)
        Y = np.array([np.logical_not(y), y]).transpose()
            
        XY = []
        for i in range(Y.shape[0]):
            XY.append((X64[i],X8[i],Y[i],s2n[i]))
        XY = np.array(XY)
        np.random.shuffle(XY)
        
        X64 = []
        X8 = []
        Y = []
        s2n = []
        for i in range(XY.shape[0]):
            X64.append(XY[i][0])
            X8.append(XY[i][1])
            Y.append(XY[i][2])
            s2n.append(XY[i][3])
        X64 = np.array(X64)
        X8 = np.array(X8)
        Y = np.array(Y)
        s2n = np.array(s2n)
        
        np.savez_compressed(timgbinPath, X64=X64, X8=X8, Y=Y, s2n=s2n)
        print("save bin fiel to %s"%(timgbinPath))
    return X64, X8, Y, s2n
    
    