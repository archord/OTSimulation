# -*- coding: utf-8 -*-
from astropy.io import fits
import numpy as np
import math
import os
import shutil
from datetime import datetime
import matplotlib.pyplot as plt

def getImgStamp(imgArray, size=12, padding = 1):
    
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
    
def getData(fotPath, totPath, destPath):
    
    timgbinPath = '%s/SIM_IMG_ALL_bin12.npz'%(destPath)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
    else:
                
        fotImgs = np.array([])
        fs2ns = np.array([])
        
        tdirs = os.listdir(fotPath)
        tdirs.sort()
        for fname in tdirs:
            if fname[-7:]=='tot.npz':
                continue
            tpath1 = "%s/%s"%(fotPath, fname)
            print(tpath1)
            fdata1 = np.load(tpath1)
            
            fotImg = fdata1['fot']
            fs2n = fdata1['fs2n']
            fotImg = getImgStamp(fotImg)
            
            if fotImgs.shape[0]==0:
                fotImgs = fotImg
                fs2ns = fs2n
            else:
                fotImgs = np.concatenate((fotImgs, fotImg), axis=0)
                fs2ns = np.concatenate((fs2ns, fs2n), axis=0)
            #break
        totImgs = np.array([])
        ts2ns = np.array([])
        
        totNum = 0
        tdirs = os.listdir(totPath)
        tdirs.sort()
        for fname in tdirs:
            tpath1 = "%s/%s"%(totPath, fname)
            print(tpath1)
            tdata1 = np.load(tpath1)
            
            totImg = tdata1['tot']
            ts2n = tdata1['ts2n']
            totImg = getImgStamp(totImg)
            
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

def getData2(fotPath, totPath, realFotPath, destPath):
    
    timgbinPath = '%s/SIM_IMG_ALL_F2T_bin12.npz'%(destPath)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
    else:
                
        fotImgs = np.array([])
        fs2ns = np.array([])
        
        tdirs = os.listdir(fotPath)
        tdirs.sort()
        for fname in tdirs:
            if fname[-7:]=='tot.npz':
                continue
            tpath1 = "%s/%s"%(fotPath, fname)
            print(tpath1)
            fdata1 = np.load(tpath1)
            
            fotImg = fdata1['fot']
            fs2n = fdata1['fs2n']
            fotImg = getImgStamp(fotImg)
            
            if fotImgs.shape[0]==0:
                fotImgs = fotImg
                fs2ns = fs2n
            else:
                fotImgs = np.concatenate((fotImgs, fotImg), axis=0)
                fs2ns = np.concatenate((fs2ns, fs2n), axis=0)
            #break
        
        tdirs = os.listdir(realFotPath)
        tdirs.sort()
        for fname in tdirs:
            if fname[-7:]=='F2T.npz':
                tpath1 = "%s/%s"%(realFotPath, fname)
                print(tpath1)
                fdata1 = np.load(tpath1)
                
                fotImg = fdata1['imgs']
                fs2n = np.zeros(fotImg.shape[0])
                
                if fotImgs.shape[0]==0:
                    fotImgs = fotImg
                    fs2ns = fs2n
                else:
                    fotImgs = np.concatenate((fotImgs, fotImg), axis=0)
                    fs2ns = np.concatenate((fs2ns, fs2n), axis=0)
                #break
                
        totImgs = np.array([])
        ts2ns = np.array([])
        
        totNum = 0
        tdirs = os.listdir(totPath)
        tdirs.sort()
        for fname in tdirs:
            tpath1 = "%s/%s"%(totPath, fname)
            print(tpath1)
            tdata1 = np.load(tpath1)
            
            totImg = tdata1['tot']
            ts2n = tdata1['ts2n']
            totImg = getImgStamp(totImg)
            
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
    
def getData3(totPath, realFotPath, destPath):
    
    timgbinPath = '%s/SIM_IMG_ALL_RealFOT_bin12.npz'%(destPath)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
    else:
                
        fotImgs = np.array([])
        fs2ns = np.array([])
                
        tdirs = os.listdir(realFotPath)
        tdirs.sort()
        for fname in tdirs:
            if fname[-7:]=='_12.npz' and fname[:3]=='fot':
                tpath1 = "%s/%s"%(realFotPath, fname)
                print(tpath1)
                fdata1 = np.load(tpath1)
                
                fotImg = fdata1['imgs']
                fs2n = np.zeros(fotImg.shape[0])
                
                if fotImgs.shape[0]==0:
                    fotImgs = fotImg
                    fs2ns = fs2n
                else:
                    fotImgs = np.concatenate((fotImgs, fotImg), axis=0)
                    fs2ns = np.concatenate((fs2ns, fs2n), axis=0)
                #break
        
        print(fotImgs.shape)
        totImgs = np.array([])
        ts2ns = np.array([])
        
        totNum = 0
        tdirs = os.listdir(totPath)
        tdirs.sort()
        for fname in tdirs:
            tpath1 = "%s/%s"%(totPath, fname)
            print(tpath1)
            tdata1 = np.load(tpath1)
            
            totImg = tdata1['tot']
            ts2n = tdata1['ts2n']
            totImg = getImgStamp(totImg)
            
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
                
        print(totImgs.shape)
        
        totNum = totImgs.shape[0]
        fotNum = fotImgs.shape[0]
        if totNum>fotNum:
            totImgs = totImgs[0:fotNum]
            ts2ns = ts2ns[0:fotNum]
        elif totNum<fotNum:
            fotImgs = fotImgs[0:totNum]
            fs2ns = fs2ns[0:totNum]
        '''
        
        totNum = 1000000
        fotNum = 1000000
        totImgs = totImgs[0:fotNum]
        ts2ns = ts2ns[0:fotNum]
        fotImgs = fotImgs[0:totNum]
        fs2ns = fs2ns[0:totNum]
        
        '''
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
    tpath3 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0927"
    
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
    
def getRealData(destPath):
    
    from gwac_util import zscale_image
    ot2path = '/home/xy/Downloads/myresource/deep_data2/simot/ot2_img_collection_180906_20180907'
    ot2listFile = '%s/list.txt'%(ot2path)
    ot2list = np.genfromtxt(ot2listFile,dtype='str')
    print(ot2list.shape)
    print(ot2list[:3])
    
    X = []
    badImgNum = 0
    badIdx = []
    
    #timgbinPath = '%s/gwac_otimg_nozscale.npz'%(destPath)
    timgbinPath = '%s/gwac_otimg.npz'%(destPath)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['ot']
        ot2prop = timgbin['ot2prop']
    else:
        for i in range(ot2list.shape[0]):
            tot2 = ot2list[i]
            objPath = "%s/%s"%(ot2path, tot2[1])
            refPath = "%s/%s"%(ot2path, tot2[2])
            diffPath = "%s/%s"%(ot2path, tot2[3])
    
            objImg = readStampFromFits(objPath)
            refImg = readStampFromFits(refPath)
            diffImg = readStampFromFits(diffPath)
            
            if objImg.shape[0]==0 or refImg.shape[0]==0 or diffImg.shape[0]==0:
                continue
            
            objImgz = zscale_image(objImg)
            refImgz = zscale_image(refImg)
            diffImgz = zscale_image(diffImg)
            '''
            objImgz = objImg
            refImgz = refImg
            diffImgz = diffImg
            '''
            #异常残差图像处理，如果scale失败：1）等于原diffImg；2）直接量化到255
            if diffImgz.shape[0]!=12 or diffImgz.shape[1]!=12:
                print("%d, %s"%(i, tot2[1]))
                badIdx.append(i)
                tmin = np.min(diffImg)
                tmax = np.max(diffImg)
                diffImgz=(((diffImg-tmin)/(tmax-tmin))*255).astype(np.uint8)
                #diffImgz = diffImg
                badImgNum = badImgNum + 1
    
            X.append([objImgz, refImgz, diffImgz])
        
        X = np.array(X)
        '''
        for i in range(X.shape[0]):
            tot2 = ot2list[i]
            tlabel = tot2[4]
            ttype = tot2[5]
            if ttype=='2':
                fig, axes = plt.subplots(1, 3, figsize=(3, 1))
                axes.flat[0].imshow(X[i][0], cmap='gray')
                axes.flat[1].imshow(X[i][1], cmap='gray')
                axes.flat[2].imshow(X[i][2], cmap='gray')
                axes.flat[1].set_title("%d, %s, look=%s, type=%s"%(i, tot2[1][:14], tlabel, ttype))
                plt.show()
        '''
        ot2prop = ot2list
        print("save bin fiel to %s"%(timgbinPath))
        np.savez_compressed(timgbinPath, ot=X, ot2prop = ot2prop)
        print("bad image %d"%(badImgNum))
    return X, ot2prop
    
def realDataApart():
            
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2"
    realDataPath2 = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart"
    tdirs = os.listdir(realDataPath)
    tdirs.sort()
    
    totimgs = np.array([])
    totprops = np.array([])
    fotimgs = np.array([])
    fotprops = np.array([])

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
        
        if totimgs.shape[0]==0:
            totimgs = totImg2
            totprops = totprop2
        else:
            if len(totImg2.shape)==4:
                totimgs = np.concatenate((totimgs, totImg2), axis=0)
                totprops = np.concatenate((totprops, totprop2), axis=0)
            
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
    
    
def realDataMinorPlant():
            
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2"
    realDataPath2 = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart"
    tdirs = os.listdir(realDataPath)
    tdirs.sort()
    
    totimgs = np.array([])
    totprops = np.array([])

    for i, fname in enumerate(tdirs):
        tpath21 = "%s/%s"%(realDataPath, fname)
        print(tpath21)
        tdata1 = np.load(tpath21)
        timgs = tdata1['imgs']
        tprops = tdata1['props']
        
        tlabel = tprops[:,5].astype(np.int)
        tot2Idx = tlabel==2
        totImg2 = timgs[tot2Idx]
        totprop2 = tprops[tot2Idx]
        
        if totimgs.shape[0]==0:
            totimgs = totImg2
            totprops = totprop2
        else:
            if len(totImg2.shape)==4:
                totimgs = np.concatenate((totimgs, totImg2), axis=0)
                totprops = np.concatenate((totprops, totprop2), axis=0)
            
    totSavePath = "%s/minorplant_all.npz"%(realDataPath2)
    np.savez_compressed(totSavePath, imgs=totimgs, props=totprops)
    print("save %d minor plant bin to %s"%(totimgs.shape[0], totSavePath))

def showImgs(tpath, showTitle, showNum=50):
    
    tdata1 = np.load(tpath)
    totImgs = tdata1['imgs']
    totProps = tdata1['props']
    
    print(showTitle)
    for i in range(totProps.shape[0]):
        tot2 = totProps[i]
        tlabel = tot2[4]
        ttype = tot2[5]

        fig, axes = plt.subplots(1, 3, figsize=(3, 1))
        axes.flat[0].imshow(totImgs[i][0], cmap='gray')
        axes.flat[1].imshow(totImgs[i][1], cmap='gray')
        axes.flat[2].imshow(totImgs[i][2], cmap='gray')
        axes.flat[1].set_title("%d, %s, look=%s, type=%s"%(i, tot2[1][:14], tlabel, ttype))
        plt.show()
        
        if i> showNum:
            break
        
        
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
        
def viewRealData():
    
    totPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart/tot_all_12.npz"
    minorPlantPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart/minorplant_all_12.npz"
    fotPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart/fot_tail_12.npz"
    
    showImgs(totPath, "\n\n**********show TOT")
    showImgs(minorPlantPath, "\n\n**********show MinorPlant")
    showImgs(fotPath, "\n\n**********show FOT")

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
    
    for i, fname in enumerate(tdirs):
        
        tpath21 = "%s/%s"%(realDataPath, fname)
        print(tpath21)
        tdata1 = np.load(tpath21)
        timgs = tdata1['imgs']
        tprops = tdata1['props']
        timgs = getImgStamp(timgs, size=12, padding = 0)
    
        dpath21 = '%s/%s_12.npz'%(realDataPath, fname[:-4])
        np.savez_compressed(dpath21, imgs=timgs, props=tprops)
        print("save %d minor plant bin to %s"%(timgs.shape[0], dpath21))
        
        #showImgs(dpath21, "\n\n**********show FOT 12")
        #break
    
    