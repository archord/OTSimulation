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
    
def getRealData(realOtPath, imgSize=8, transMethod='none'):
    
    otImgs = np.array([])
    props = np.array([])
            
    #realFotPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart"
    tdirs = os.listdir(realOtPath)
    tdirs.sort()
            
    for i, fname in enumerate(tdirs):
        tpath21 = "%s/%s"%(realOtPath, fname)
        print(tpath21)
        data1 = np.load(tpath21)
        otImg = data1['imgs']
        prop = data1['props']
        
        otImg = getImgStamp(otImg, size=imgSize, padding = 0, transMethod='none')
        
        if otImgs.shape[0]==0:
            otImgs = otImg
            props = prop
        else:
            otImgs = np.concatenate((otImgs, otImg), axis=0)
            props = np.concatenate((props, prop), axis=0)
        #break
    
    print(otImgs.shape)
        
    return otImgs, props
    
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
    
    