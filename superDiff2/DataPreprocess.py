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
from PIL import Image
from random import random

'''
preMethod: 
1, eachMax: obj tmp and resi transform to 255 by each maxValue(three max value)
2, unionMax: obj tmp and resi transform to 255 by union maxValue(one max value)
3, zscale: obj tmp and resi transform to 255 by zscale 
4, none: donot execuate any operation
'''
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

def dataAugment(srcPath):
    
    timgbinPath = '%s_aug.npz'%(srcPath[:-4])
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
    else:
        print(srcPath)
        timgbin = np.load(srcPath)
        X = timgbin['X']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
        
        print("before augment %d"%(X.shape[0]))
        X1 = np.rot90(X, 1, (2,3))
        X2 = np.rot90(X1, 1, (2,3))
        X3 = np.rot90(X2, 1, (2,3))
        
        X = np.concatenate((X, X1, X2, X3), axis=0)
        Y = np.concatenate((Y, Y, Y, Y), axis=0)
        s2n = np.concatenate((s2n, s2n, s2n, s2n), axis=0)
        
        print("after augment %d"%(Y.shape[0]))
    
        np.savez_compressed(timgbinPath, X=X, Y=Y, s2n=s2n)
        print("save bin fiel to %s"%(timgbinPath))
    return X, Y, s2n

'''
preMethod: 
1, eachMax: obj tmp and resi transform to 255 by each maxValue(three max value)
2, unionMax: obj tmp and resi transform to 255 by union maxValue(one max value)
3, zscale: obj tmp and resi transform to 255 by zscale 
4, none: donot execuate any operation
'''
def getData(totPath, fotPath, destPath, imgSize=8, transMethod='none'):
    
    timgbinPath = '%s/SIM_TOT_REAL_FOT_bin_%s%d.npz'%(destPath, transMethod, imgSize)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
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
        
        fotImgs = np.array([])
        fs2ns = np.array([])
        for i, fname in enumerate(fotImgfiles):
            #if fname[:3]=='fot':
                tpath21 = "%s/%s"%(fotPath, fname)
                print(tpath21)
                fdata1 = np.load(tpath21)
                fotImg = fdata1['imgs']
                fprops = fdata1['parms']
                
                if fotImg.shape[0]>600:
                    continue
                
                fotImg = getImgStamp(fotImg, size=imgSize, padding = 1, transMethod='none')
                #fs2n = np.zeros(fotImg.shape[0])
                fs2n = 1.087/fprops[:,12].astype(np.float)
                
                if fotImgs.shape[0]==0:
                    fotImgs = fotImg
                    fs2ns = fs2n
                else:
                    fotImgs = np.concatenate((fotImgs, fotImg), axis=0)
                    fs2ns = np.concatenate((fs2ns, fs2n), axis=0)
                #break
        
        
        badImgs = np.array([])
        bads2ns = np.array([])
        for i, fname in enumerate(badImgfiles):
            #if fname[:3]=='fot':
                tpath21 = "%s/%s"%(fotPath, fname)
                print(tpath21)
                fdata1 = np.load(tpath21)
                fotImg = fdata1['imgs']
                fprops = fdata1['parms']
                
                if fotImg.shape[0]>600:
                    continue
                
                fotImg = getImgStamp(fotImg, size=imgSize, padding = 1, transMethod='none')
                fs2n = np.zeros(fotImg.shape[0])
                #fs2n = 1.087/fprops[:,12].astype(np.float)
                
                if badImgs.shape[0]==0:
                    badImgs = fotImg
                    bads2ns = fs2n
                else:
                    badImgs = np.concatenate((badImgs, fotImg), axis=0)
                    bads2ns = np.concatenate((bads2ns, fs2n), axis=0)
                #break
        
        print("fotSize %d"%(fotImgs.shape[0]))
        print("badSize %d"%(badImgs.shape[0]))
        
        XY = []
        for i in range(badImgs.shape[0]):
            XY.append((badImgs[i],bads2ns[i]))
        XY = np.array(XY)
        np.random.shuffle(XY)
        
        X = []
        s2n = []
        for i in range(XY.shape[0]):
            X.append(XY[i][0])
            s2n.append(XY[i][1])
        badImgs = np.array(X)
        bads2ns = np.array(s2n)
        
        print("badSize %d"%(badImgs.shape[0]))
        print("bads2ns %d"%(bads2ns.shape[0]))
        
        fotImgsNum = fotImgs.shape[0]
        badImgs = badImgs[:int(fotImgsNum/10)]
        bads2ns = bads2ns[:int(fotImgsNum/10)]
        print("badSize %d"%(badImgs.shape[0]))
        print("bads2ns %d"%(bads2ns.shape[0]))
        
        fotImgs = np.concatenate((fotImgs, badImgs), axis=0)
        fs2ns = np.concatenate((fs2ns, bads2ns), axis=0)
        print("fotImgs %d"%(fotImgs.shape[0]))
        print("fs2ns %d"%(fs2ns.shape[0]))
        
        totImgs = np.array([])
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
            totImg = getImgStamp(totImg, size=imgSize, padding = 1, transMethod='none')
            
            if totImgs.shape[0]==0:
                totImgs = totImg
                ts2ns = ts2n
            else:
                totImgs = np.concatenate((totImgs, totImg), axis=0)
                ts2ns = np.concatenate((ts2ns, ts2n), axis=0)
            
            totNum = totNum + totImg.shape[0]
            if totNum >= fotImgs.shape[0]:
                break
            #break
                
        print("totSize %d"%(totImgs.shape[0]))
        
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
        
        np.savez_compressed(timgbinPath, X=X, Y=Y, s2n=s2n)
        print("save bin fiel to %s"%(timgbinPath))
    return X, Y, s2n
    
def getData2(totPath, fotPath, destPath, tNamePart, imgSize=64, transMethod='none'):
    
    timgbinPath = '%s/SIM_TOT_REAL_FOT_bin_%s_%s.npz'%(destPath, transMethod, tNamePart)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
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
        
        fotImgs = np.array([])
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
                
                fotImg = getImgStamp(fotImg, size=imgSize, padding = 1, transMethod='none')
                #fs2n = np.zeros(fotImg.shape[0])
                fs2n = 1.087/fprops[:,12].astype(np.float)
                
                if fotImgs.shape[0]==0:
                    fotImgs = fotImg
                    fs2ns = fs2n
                else:
                    fotImgs = np.concatenate((fotImgs, fotImg), axis=0)
                    fs2ns = np.concatenate((fs2ns, fs2n), axis=0)
                if fotImgs.shape[0]>50000:
                    break
                
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
        
        
        badImgs = np.array([])
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
                
                fotImg = getImgStamp(fotImg, size=imgSize, padding = 1, transMethod='none')
                fs2n = np.zeros(fotImg.shape[0])
                #fs2n = 1.087/fprops[:,12].astype(np.float)
                
                if badImgs.shape[0]==0:
                    badImgs = fotImg
                    bads2ns = fs2n
                else:
                    badImgs = np.concatenate((badImgs, fotImg), axis=0)
                    bads2ns = np.concatenate((bads2ns, fs2n), axis=0)
                if badImgs.shape[0]>50000:
                    break
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
        
        print("fotSize %d"%(fotImgs.shape[0]))
        print("badSize %d"%(badImgs.shape[0]))
        
        fotImgs = np.concatenate((fotImgs, badImgs), axis=0)
        fs2ns = np.concatenate((fs2ns, bads2ns), axis=0)
        print("fotImgs %d"%(fotImgs.shape[0]))
        print("fs2ns %d"%(fs2ns.shape[0]))
        
        totImgs = np.array([])
        ts2ns = np.array([])
        
        totNum = 0
        tdirs = os.listdir(totPath)
        tdirs.sort()
        for i, fname in enumerate(tdirs):
            tpath1 = "%s/%s"%(totPath, fname)
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
            if totNum >= fotImgs.shape[0]:
                break
            #break
                
        print("totSize %d"%(totImgs.shape[0]))
        
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
        
        np.savez_compressed(timgbinPath, X=X, Y=Y, s2n=s2n)
        print("save bin fiel to %s"%(timgbinPath))
    return X, Y, s2n
    
def viewData():
    
    tpath1 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0924"
    tpath2 = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2"
    tpath3 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0929"
    
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    X,Y,s2n = getData(tpath1, tpath3, workPath)
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    
    showNum=50
    tnum = 0
    print("\n\n***********************")
    print("True image")
    ts2n = []
    for i in range(X.shape[0]):
        if Y[i, 1]==1:
            if tnum<showNum:
                plt.clf()
                fig, axes = plt.subplots(1, 3, figsize=(3, 3))
                axes.flat[0].imshow(X[i][0], interpolation = "nearest", cmap='gray')
                axes.flat[1].imshow(X[i][1], interpolation = "nearest", cmap='gray')
                axes.flat[2].imshow(X[i][2], interpolation = "nearest", cmap='gray')
                axes.flat[2].set_title("predicted label = " + str(Y[i, 1]) + 
                                              ", s2n = " + str(s2n[i]))
                plt.show()
                tnum = tnum + 1
            ts2n.append(s2n[i])
    
    tnum = 0
    print("\n\n***********************")
    print("False image")
    fs2n = []
    for i in range(X.shape[0]):
        if Y[i, 1]==0:
            if tnum<showNum:
                plt.clf()
                fig, axes = plt.subplots(1, 3, figsize=(3, 3))
                axes.flat[0].imshow(X[i][0], interpolation = "nearest", cmap='gray')
                axes.flat[1].imshow(X[i][1], interpolation = "nearest", cmap='gray')
                axes.flat[2].imshow(X[i][2], interpolation = "nearest", cmap='gray')
                axes.flat[2].set_title("predicted label = " + str(Y[i, 1]) + 
                                              ", s2n = " + str(s2n[i]))
                plt.show()
                tnum = tnum + 1
            fs2n.append(s2n[i])


    magerr = ts2n

    from matplotlib.ticker import MultipleLocator, FormatStrFormatter
    xmajorLocator   = MultipleLocator(5)
    xminorLocator   = MultipleLocator(2)

    plt.figure(figsize = (16, 8))
    ax = plt.subplot(111)
    plt.hist(magerr, bins=20, range=(0,100), normed=False,     
            weights=None, cumulative=False, bottom=None,     
            histtype=u'bar', align=u'left', orientation=u'vertical',     
            rwidth=0.8, log=False, color=None, label=None, stacked=False,     
            hold=None) 
    ax.xaxis.set_major_locator(xmajorLocator)
    ax.xaxis.set_minor_locator(xminorLocator)
    plt.show()
    
    xmajorLocator   = MultipleLocator(2)
    xminorLocator   = MultipleLocator(1)
    plt.figure(figsize = (16, 8))
    ax = plt.subplot(111)
    plt.hist(magerr, bins=20, range=(0,20), normed=False,     
            weights=None, cumulative=False, bottom=None,     
            histtype=u'bar', align=u'left', orientation=u'vertical',     
            rwidth=0.8, log=False, color=None, label=None, stacked=False,     
            hold=None) 
    ax.xaxis.set_major_locator(xmajorLocator)
    ax.xaxis.set_minor_locator(xminorLocator)
    plt.show()
    
    magerr = fs2n

    xmajorLocator   = MultipleLocator(5)
    xminorLocator   = MultipleLocator(2)

    plt.figure(figsize = (16, 8))
    ax = plt.subplot(111)
    plt.hist(magerr, bins=20, range=(0,100), normed=False,     
            weights=None, cumulative=False, bottom=None,     
            histtype=u'bar', align=u'left', orientation=u'vertical',     
            rwidth=0.8, log=False, color=None, label=None, stacked=False,     
            hold=None) 
    ax.xaxis.set_major_locator(xmajorLocator)
    ax.xaxis.set_minor_locator(xminorLocator)
    plt.show()
    
    xmajorLocator   = MultipleLocator(2)
    xminorLocator   = MultipleLocator(1)
    plt.figure(figsize = (16, 8))
    ax = plt.subplot(111)
    plt.hist(magerr, bins=20, range=(0,20), normed=False,     
            weights=None, cumulative=False, bottom=None,     
            histtype=u'bar', align=u'left', orientation=u'vertical',     
            rwidth=0.8, log=False, color=None, label=None, stacked=False,     
            hold=None) 
    ax.xaxis.set_major_locator(xmajorLocator)
    ax.xaxis.set_minor_locator(xminorLocator)
    plt.show()

def readStampFromFits(filename, size=12):
    
    rst = np.array([])
    with fits.open(filename,memmap=False) as ft:
        
        data = ft[0].data
        padding = -1
        imgSize = data.shape[0]
        ctrIdx = math.ceil(imgSize/2.0) - 1
        halfWid = math.floor(size/2.0)
        minIdx = ctrIdx - halfWid - padding
        maxIdx = ctrIdx + halfWid - padding
        rst = data[minIdx:maxIdx,minIdx:maxIdx]
        
    return rst
    
def getElongData(realOtPath, destPath, elongMin=0.7, elongMax=1.0):
    
    timgbinPath = '%s/REAL_ELONG_DATA_bin_e%.0f.npz'%(destPath,elongMin*10)
    #if os.path.exists(timgbinPath):
    if False:
        print("bin file exist, read from %s"%(timgbinPath))
        #timgbin = np.load(timgbinPath)
        #imgs = timgbin['imgs']
        #parms = timgbin['parms']
    else:
    
        imgs = np.array([])
        parms = np.array([])
        
        tdirs = os.listdir(realOtPath)
        tdirs.sort()
        
        for i, fname in enumerate(tdirs):
            
            try:
                if fname.find('bad')>-1 and i>10009:
                    tpath21 = "%s/%s"%(realOtPath, fname)
                    print("%d:%s"%(i,tpath21))
                    data1 = np.load(tpath21)
                    otImg = data1['imgs']
                    prop = data1['parms']
                    
                    tIdx = (prop[:,6]>elongMin) & (prop[:,6]<elongMax)
                    otImg = otImg[tIdx]
                    prop = prop[tIdx]
                    
                    if prop.shape[0]>0 and len(otImg.shape)==4:
                        if imgs.shape[0]==0:
                            imgs = otImg
                            parms = prop
                        else:
                            imgs = np.concatenate((imgs, otImg), axis=0)
                            parms = np.concatenate((parms, prop), axis=0)
                    print(imgs.shape)
                    if imgs.shape[0]>10000:
                        timgbinPath = '%s/REAL_ELONG_DATA_bin_e%.0f_%04d_%07d.npz'%(destPath,elongMin*10, i, imgs.shape[0])
                        np.savez_compressed(timgbinPath, imgs=imgs, parms=parms)
                        print("save bin fiel to %s"%(timgbinPath))
                        imgs = np.array([])
                        parms = np.array([])
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
                
        print("total get %d ELONGATION"%(imgs.shape[0]))
        
        timgbinPath = '%s/REAL_ELONG_DATA_bin_e%.0f_%04d_%07d.npz'%(destPath,elongMin*10, i, imgs.shape[0])
        np.savez_compressed(timgbinPath, imgs=imgs, parms=parms)
        print("save bin fiel to %s"%(timgbinPath))
    return timgbinPath

def shuffleData(X, Y, s2n):
    
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
    
    return X, Y, s2n
        
def getFinalTestData(totPath, fotPath1, fotPath2, realDataPath, destPath, imgSize=64, transMethod='none'):
    
    timgbinPath = '%s/FINAL_TEST_ADD_REAL_DATA_bin_%s.npz'%(destPath, transMethod)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
    else:
        
        dateStr = '20190122'
        tSampleNamePart = "64_fot10w_%s"%(dateStr)
        X0,Y0,s2n0 = getRealData(realDataPath, destPath, tSampleNamePart)    
        tIdx = [370,389,419,451,459,557,559,579,3463,5238,7010,7131,7460,7748,9139,9698,12605,13183,20547,20554,20558,20561,20566,20568,20575,20586,20589,20642,20644,20646,20648,20717,20726,20730,20734,20736,20739,20746,20768,20771,20868,20871,20884,20885]
        tIdx = np.array(tIdx)
        X0 = X0[tIdx]
        Y0 = Y0[tIdx]
        s2n0 = s2n0[tIdx]
    
        totImgs = np.array([])
        tprops = np.array([])        
        totBins = os.listdir(totPath)
        totBins.sort()
        
        rNum = int(random()*100)+5
        tnum = len(totBins)
        for i in range(tnum-rNum, tnum-rNum+5):
            
            try:
                tpath21 = "%s/%s"%(totPath, totBins[i])
                print("%d:%s"%(i,tpath21))
                data1 = np.load(tpath21)
                otImg = data1['tot']
                prop = data1['ts2n']
                
                otImg = getImgStamp(otImg, size=imgSize, padding = 1, transMethod='none')
                ots2n = prop
                
                if totImgs.shape[0]==0:
                    totImgs = otImg
                    tprops = ots2n
                else:
                    totImgs = np.concatenate((totImgs, otImg), axis=0)
                    tprops = np.concatenate((tprops, ots2n), axis=0)
                #break
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
                
        otSize = totImgs.shape[0]
        y = np.ones(otSize)
        tY = np.array([np.logical_not(y), y]).transpose()
        totImgs, tY, tprops = shuffleData(totImgs, tY, tprops)
        
        fotImgs1 = np.array([])
        fprops1 = np.array([])
        fotBins1 = ['REAL_ELONG_DATA_bin_e7_1946_0005173.npz','REAL_ELONG_DATA_bin_e7_1521_0010009.npz']
        fotBins1Sel = ['REAL_ELONG_DATA_bin_e7_1946_0005173Sel.txt','REAL_ELONG_DATA_bin_e7_1521_0010009Sel.txt']
        
        for i in range(0, 2):
            
            try:
                tpath21 = "%s/%s"%(fotPath1, fotBins1[i])
                print("%d:%s"%(i,tpath21))
                data1 = np.load(tpath21)
                otImg = data1['imgs']
                prop = data1['parms']
                
                idxFile  = "%s/%s"%(fotPath1, fotBins1Sel[i])
                tidx = np.loadtxt(idxFile, dtype=np.int)
                otImg=otImg[tidx]
                prop=prop[tidx]
                
                otImg = getImgStamp(otImg, size=imgSize, padding = 1, transMethod='none')
                ots2n = 1.087/prop[:,12].astype(np.float)
                
                if fotImgs1.shape[0]==0:
                    fotImgs1 = otImg
                    fprops1 = ots2n
                else:
                    fotImgs1 = np.concatenate((fotImgs1, otImg), axis=0)
                    fprops1 = np.concatenate((fprops1, ots2n), axis=0)
                #break
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
                
        otSize = fotImgs1.shape[0]
        y = np.zeros(otSize)
        fY1 = np.array([np.logical_not(y), y]).transpose()
        
        fotImgs2 = np.array([])
        fprops2 = np.array([])
        fotBins2 = os.listdir(fotPath2)
        fotBins2.sort()
        
        rNum = int(random()*500)+50
        tnum = len(fotBins2)
        for i in range(tnum-rNum, tnum-rNum+40):
            
            try:
                tname = fotBins2[i]
                if tname.find('fot')>-1:
                    tpath21 = "%s/%s"%(fotPath2, tname)
                    print("%d:%s"%(i,tpath21))
                    data1 = np.load(tpath21)
                    otImg = data1['imgs']
                    prop = data1['parms']
                    
                    otImg = getImgStamp(otImg, size=imgSize, padding = 1, transMethod='none')
                    ots2n = 1.087/prop[:,12].astype(np.float)
                    
                    if fotImgs2.shape[0]==0:
                        fotImgs2 = otImg
                        fprops2 = ots2n
                    else:
                        fotImgs2 = np.concatenate((fotImgs2, otImg), axis=0)
                        fprops2 = np.concatenate((fprops2, ots2n), axis=0)
                    #break
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
                
        otSize = fotImgs2.shape[0]
        y = np.zeros(otSize)
        fY2 = np.array([np.logical_not(y), y]).transpose()
        fotImgs2, fY2, fprops2 = shuffleData(fotImgs2, fY2, fprops2)
        
        print("number: tot=%d, fot1=%d, fot2=%d"%(totImgs.shape[0],fotImgs1.shape[0],fotImgs2.shape[0]))
        totImgs, tY, tprops = totImgs[0:2000], tY[0:2000], tprops[0:2000]
        fotImgs1, fY1, fprops1 = fotImgs1[0:1000], fY1[0:1000], fprops1[0:1000]
        fotImgs2, fY2, fprops2 = fotImgs2[0:1000], fY2[0:1000], fprops2[0:1000]
        
        fotImgs1[-len(X0):]=X0
        
        X = np.concatenate((totImgs, fotImgs1, fotImgs2), axis=0)
        Y = np.concatenate((tY, fY1, fY2), axis=0)
        s2n = np.concatenate((tprops, fprops1, fprops2), axis=0)
            
        np.savez_compressed(timgbinPath, X=X, Y=Y, s2n=s2n)
        print("save bin fiel to %s"%(timgbinPath))
    return X, Y, s2n
    
def getRealData(realOtPath, destPath, tNamePart, imgSize=64, transMethod='none'):
    
    timgbinPath = '%s/SIM_REAL_DATA_bin_%s_%s.npz'%(destPath, transMethod, tNamePart)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
    else:
    
        otImgs = np.array([])
        props = np.array([])
        
        tdirs = os.listdir(realOtPath)
        tdirs.sort()
                
        for i, fname in enumerate(tdirs):
            
            try:
                tpath21 = "%s/%s"%(realOtPath, fname)
                print("%d:%s"%(i,tpath21))
                data1 = np.load(tpath21)
                otImg = data1['imgs']
                prop = data1['parms']
                
                otImg = getImgStamp(otImg, size=imgSize, padding = 1, transMethod='none')
                ots2n = 1.087/prop[:,12].astype(np.float)
                
                if otImgs.shape[0]==0:
                    otImgs = otImg
                    props = ots2n
                else:
                    otImgs = np.concatenate((otImgs, otImg), axis=0)
                    props = np.concatenate((props, ots2n), axis=0)
                #break
            except Exception as e:
                tstr = traceback.format_exc()
                print(tstr)
                
        otSize = otImgs.shape[0]
        otLabel = np.zeros(otSize)
        X = otImgs
        s2n = props
        y = otLabel
        Y = np.array([np.logical_not(y), y]).transpose()
        
        np.savez_compressed(timgbinPath, X=X, Y=Y, s2n=s2n)
        print("save bin fiel to %s"%(timgbinPath))
            
    return X, Y, s2n
    
def getRealData2(realOtPath, imgSize=8, transMethod='none'):
        
    totPath = "%s/tot_all.npz"%(realOtPath)
    mpPath = "%s/minorplant_all.npz"%(realOtPath)
    
    tots = np.load(totPath)
    mps = np.load(mpPath)
    
    totImgs = tots['imgs']
    totprops = tots['props']
    totImgs = getImgStamp(totImgs, size=imgSize, padding = 0, transMethod='none')
    
    
    mpImgs = mps['imgs']
    mpprops = mps['props']
    mpImgs = getImgStamp(mpImgs, size=imgSize, padding = 0, transMethod='none')
    
    imgs = np.concatenate((totImgs, mpImgs), axis=0)
    props = np.concatenate((totprops, mpprops), axis=0)
        
    return imgs, props
    
def realDataApart():
            
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2"
    realDataPath2 = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart"
    tdirs = os.listdir(realDataPath)
    tdirs.sort()
    
    totimgs = np.array([])
    totprops = np.array([])
    fotimgs = np.array([])
    fotprops = np.array([])
    mpimgs = np.array([])
    mpprops = np.array([])

    for i, fname in enumerate(tdirs):
        tpath21 = "%s/%s"%(realDataPath, fname)
        print(tpath21)
        tdata1 = np.load(tpath21)
        timgs = tdata1['imgs']
        tprops = tdata1['props']
        
        tlabel = tprops[:,4].astype(np.int)
        tot2Idx = tlabel==1
        fot2Idx = tlabel>1
        totImg2 = timgs[tot2Idx]
        totprop2 = tprops[tot2Idx]
        fotImg2 = timgs[fot2Idx]
        fotprop2 = tprops[fot2Idx]
        
        ttype = tprops[:,5].astype(np.int)
        mpIdx = ttype==2
        mpimg = timgs[mpIdx]
        mpprop = tprops[mpIdx]
        
        if totimgs.shape[0]==0:
            totimgs = totImg2
            totprops = totprop2
        else:
            if len(totImg2.shape)==4:
                totimgs = np.concatenate((totimgs, totImg2), axis=0)
                totprops = np.concatenate((totprops, totprop2), axis=0)
                
        if mpimgs.shape[0]==0:
            mpimgs = mpimg
            mpprops = mpprop
        else:
            if len(mpimg.shape)==4:
                mpimgs = np.concatenate((mpimgs, mpimg), axis=0)
                mpprops = np.concatenate((mpprops, mpprop), axis=0)
            
        if fotimgs.shape[0]==0:
            fotimgs = fotImg2
            fotprops = fotprop2
        else:
            if len(fotImg2.shape)==4:
                fotimgs = np.concatenate((fotimgs, fotImg2), axis=0)
                fotprops = np.concatenate((fotprops, fotprop2), axis=0)
        
        if fotimgs.shape[0]>=200000:
            fotSavePath = "%s/fot_%03d.npz"%(realDataPath2,i+1)
            np.savez_compressed(fotSavePath, imgs=fotimgs, props=fotprops)
            print("save %d fot bin to %s"%(fotimgs.shape[0], fotSavePath))
            fotimgs = np.array([])
            fotprops = np.array([])
        #if i>4:
        #    break
        
    fotSavePath = "%s/fot_tail.npz"%(realDataPath2)
    np.savez_compressed(fotSavePath, imgs=fotimgs, props=fotprops)
    print("save %d fot bin to %s"%(fotimgs.shape[0], fotSavePath))
            
    totSavePath = "%s/tot_all.npz"%(realDataPath2)
    np.savez_compressed(totSavePath, imgs=totimgs, props=totprops)
    print("save %d tot bin to %s"%(totimgs.shape[0], totSavePath))
    
    mpSavePath = "%s/minorplant_all.npz"%(realDataPath2)
    np.savez_compressed(mpSavePath, imgs=mpimgs, props=mpprops)
    print("save %d minor plant bin to %s"%(mpimgs.shape[0], mpSavePath))
    
def showImgs(tpath, showTitle, showNum=50):
    
    tdata1 = np.load(tpath)
    totImgs = tdata1['imgs']
    totProps = tdata1['props']
    
    print(showTitle)
    for i in range(totProps.shape[0]):
        tot2 = totProps[i]
        tlabel = tot2[4]
        ttype = tot2[5]
        #print(tot2)

        fig, axes = plt.subplots(1, 3, figsize=(3, 1))
        axes.flat[0].imshow(totImgs[i][0], cmap='gray')
        axes.flat[1].imshow(totImgs[i][1], cmap='gray')
        axes.flat[2].imshow(totImgs[i][2], cmap='gray')
        axes.flat[1].set_title("%d, %s, look=%s, type=%s, s2n=%s"%(i, tot2[1][:14], tlabel, ttype, tot2[8]))
        plt.show()
        
        if i> showNum:
            break
        
def viewRealData():
    
    totPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart/tot_all_12.npz"
    minorPlantPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart/minorplant_all_12.npz"
    fotPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart/fot_tail_12.npz"
    ttPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2/GWAC_OT_ALL_0001000.npz"
    
    #showImgs(totPath, "\n\n**********show TOT")
    #showImgs(minorPlantPath, "\n\n**********show MinorPlant")
    #showImgs(fotPath, "\n\n**********show FOT")
    showImgs(ttPath, "\n\n**********show GWAC_OT_ALL_0001000.npz")
        
def showImgs2(tpath, showTitle, showNum=50):
    
    tdata1 = np.load(tpath)
    totImgs = tdata1['tot']
    ts2n = tdata1['ts2n']
    
    print(showTitle)
    for i in range(totImgs.shape[0]):

        fig, axes = plt.subplots(1, 3, figsize=(3, 1))
        axes.flat[0].imshow(totImgs[i][0], cmap='gray')
        axes.flat[1].imshow(totImgs[i][1], cmap='gray')
        axes.flat[2].imshow(totImgs[i][2], cmap='gray')
        axes.flat[1].set_title("%d, s2n=%f"%(i, ts2n[i]))
        plt.show()
        
        if i> showNum:
            break

def viewSimData():
    tpath1 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0928"
    
    tdirs = os.listdir(tpath1)
    tdirs.sort()
    for ii, fname in enumerate(tdirs):
        if ii<10 or ii>590:
            tpath11 = "%s/%s"%(tpath1, fname)
            showImgs2(tpath11, fname, showNum=20)
    
def resizeRealData():
    
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart"
    tdirs = os.listdir(realDataPath)
    tdirs.sort()
    
    imgSize = 8
    for i, fname in enumerate(tdirs):
        
        tpath21 = "%s/%s"%(realDataPath, fname)
        print(tpath21)
        tdata1 = np.load(tpath21)
        timgs = tdata1['imgs']
        tprops = tdata1['props']
        timgs = getImgStamp(timgs, size=imgSize, padding = 0)
    
        dpath21 = '%s/%s_%d.npz'%(realDataPath, fname[:-4], imgSize)
        np.savez_compressed(dpath21, imgs=timgs, props=tprops)
        print("save %d minor plant bin to %s"%(timgs.shape[0], dpath21))
        
        #showImgs(dpath21, "\n\n**********show FOT 12")
        #break

def saveImgs(imgs, tpath, zoomScale=4):
    
    if not os.path.exists(tpath):
        os.system("mkdir -p %s"%(tpath))
    
    for i in range(imgs.shape[0]):
        X = imgs[i]
        tobjImg = zscale_image(X[0])
        tTempImg = zscale_image(X[1])
        tResiImg = zscale_image(X[2])
        
        if zoomScale!=1:
            tobjImg = scipy.ndimage.zoom(tobjImg, zoomScale, order=0)
            tTempImg = scipy.ndimage.zoom(tTempImg, zoomScale, order=0)
            tResiImg = scipy.ndimage.zoom(tResiImg, zoomScale, order=0)
        xspace = np.ones((tobjImg.shape[0],10), np.uint8)*255
        timg = np.concatenate((tobjImg, xspace, tTempImg, xspace, tResiImg), axis=1)
        
        savePath = "%s/%05d.jpg"%(tpath,i)
        Image.fromarray(timg).save(savePath)
        
        