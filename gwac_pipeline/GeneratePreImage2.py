# -*- coding: utf-8 -*-
import os
from PIL import Image
import numpy as np
import scipy.ndimage
import math
from astropy.io import fits

def getBkg(imgData):
    
    samples = imgData.flatten()
    samples.sort()
    chop_size = int(0.1*len(samples))
    bkgSubset = samples[:-chop_size]
    bkg = np.median(bkgSubset)
    return bkg

def zscale_image(input_img, contrast=0.25):

    """This emulates ds9's zscale feature. Returns the suggested minimum and
    maximum values to display."""
    
    #samples = input_img.flatten()
    samples = input_img[input_img>0]
    samples = samples[~np.isnan(samples)]
    samples.sort()
    chop_size = int(0.1*len(samples))
    subset = samples[chop_size:-chop_size]
    
    if len(subset)<10:
        return np.array([])

    i_midpoint = int(len(subset)/2)
    I_mid = subset[i_midpoint]

    fit = np.polyfit(np.arange(len(subset)) - i_midpoint, subset, 1)
    # fit = [ slope, intercept]

    z1 = I_mid + fit[0]/contrast * (1-i_midpoint)/1.0
    z2 = I_mid + fit[0]/contrast * (len(subset)-i_midpoint)/1.0
    zmin = z1
    zmax = z2
    
    if zmin<0:
        zmin=0
    if math.fabs(zmin-zmax)<0.000001:
        zmin = np.min(samples)
        zmax = np.max(samples)
    
    zimg = input_img.copy()
    zimg[zimg>zmax] = zmax
    zimg[zimg<zmin] = zmin
    zimg=(((zimg-zmin)/(zmax-zmin))*255).astype(np.uint8)
    
    return zimg


def getFullAndSubThumbnail(imgPath, imgName):

    fpath = "%s/%s"%(imgPath, imgName)
    tdata = fits.getdata(fpath)
    
    subImg = getThumbnail_(tdata, stampSize=(100,100), grid=(5, 5), innerSpace = 1, border=100)
    #fullImg = getFullThumbnail_(tdata,zoomFraction=0.5)
    fullImg = np.array([])
    
    return fullImg, subImg
    
'''
对图像均匀接取grid=width_num*height_num个子窗口图像，每个窗口图像的大小为stampSize=(stampW, stapmH)
grid可以等于(1,1)
innerSpace可以等于0
'''
def getThumbnail_(tdata, stampSize=(500,500), grid=(3, 3), innerSpace = 1, contrast=0.25, border=0):
    
    imgSize = tdata.shape
    imgW = imgSize[1]
    imgH = imgSize[0]
    halfStampW = int(stampSize[0]/2)
    halfStampH = int(stampSize[1]/2)

    if grid[0]>1 and grid[1]>1:
        startX = halfStampW + border
        endX = imgW - halfStampW - border
        startY = halfStampH + border
        endY = imgH - halfStampH - border
        XInterval = int((endX-startX)/(grid[0]-1))
        YInterval = int((endY-startY)/(grid[1]-1))
        
        subRegions = []
        for y in range(grid[1]):
            centerY = startY + y*YInterval
            minY = centerY - halfStampH
            maxY = centerY + halfStampH
            if minY<0:
                minY=0
            if maxY>imgH:
                maxY = imgH
            for x in range(grid[0]):
                centerX = startX + x*XInterval
                minX = centerX - halfStampW
                maxX = centerX + halfStampW
                if minX<0:
                    minX=0
                if maxX>imgW:
                    maxX = imgW
                subRegions.append((minY, maxY, minX, maxX))
        
        #print(subRegions)
        stampImgs = []
        for treg in subRegions:
            timg = tdata[treg[0]:treg[1], treg[2]:treg[3]]
            
            #tbkg = getBkg(timg)
            #timg = timg-tbkg
            timgz = zscale_image(timg, contrast=0.25)
            if timgz.shape[0] == 0:
                timgz = timg
                tmin = np.min(timgz)
                tmax = np.max(timgz)
                timgz=(((timgz-tmin)/(tmax-tmin))*255).astype(np.uint8)
            stampImgs.append(timgz)
        
        for y in range(grid[1]):
            for x in range(grid[0]):
                tidx = y*grid[0] + x
                timg = stampImgs[tidx]
                if x ==0:
                    rowImg = timg
                else:
                    xspace = np.ones((timg.shape[0],innerSpace), np.uint8)*255
                    rowImg = np.concatenate((rowImg, xspace, timg), axis=1)
            if y ==0:
                conImg = rowImg
            else:
                yspace = np.ones((innerSpace,rowImg.shape[1]), np.uint8)*255
                conImg = np.concatenate((conImg, yspace, rowImg), axis=0)
    else:
        ctrX = math.ceil(imgW/2)-1
        ctrY = math.ceil(imgH/2)-1
        startX = ctrX - halfStampW
        endX = ctrX + halfStampW
        startY = ctrY - halfStampH
        endY = ctrY + halfStampH
        if startX<0:
            startX=0
        if endX>=imgH:
            endX = imgH-1
        if startY<0:
            startY=0
        if endY>=imgW:
            endY = imgW-1
        timg = tdata[startY:endY, startX:endX]
        timgz = zscale_image(timg, contrast=0.25)
        if timgz.shape[0] == 0:
            timgz = timg
            tmin = np.min(timgz)
            tmax = np.max(timgz)
            timgz=(((timgz-tmin)/(tmax-tmin))*255).astype(np.uint8)
        conImg = timgz
        
    return conImg

def genOneDate(tdateStr):

    srcPath = "/data/gwac_data/gwac_orig_fits"
    destPath = "/data/gwac_data/thumbnail"
    spath1 = "%s/%s"%(srcPath, tdateStr)
    dpath1 = "%s/%s"%(destPath, tdateStr)
    tempName = 'G043_mon_objt_181025T12592921.fit.fz'
    tempNameLen = len(tempName)
    
    if not os.path.exists(spath1):
        print("generate error, %s does not exist"%(spath1))
        return
        
    if not os.path.exists(dpath1):
        os.system("mkdir %s"%(dpath1))
    
    ccdDirs = os.listdir(spath1)
    ccdDirs.sort(reverse=True)
    for tccd in ccdDirs:
        tccdName = tccd[0] + tccd[5:8]
        spath2 = "%s/%s"%(spath1, tccd)
        dpath2 = "%s/%s"%(dpath1, tccdName)
        if not os.path.exists(dpath2):
            os.system("mkdir %s"%(dpath2))
        
        print(tccd)
        fzimgs = os.listdir(spath2)
        fzimgs.sort()
        fzimgs2 = []
        for timg in fzimgs:
            if len(timg)==tempNameLen:
                fzimgs2.append(timg)
        
        tnum = 0
        for ii, timg in enumerate(fzimgs2):
            if ii%20==1:
                imgName = timg.split(".")[0]
                #spath3 = "%s/%s"%(spath2, timg)
                #dpath31 = "%s/%s.jpg"%(dpath2, imgName)
                dpath32 = "%s/%s_min.jpg"%(dpath2, imgName)
                fullImg, subImg = getFullAndSubThumbnail(spath2, timg)
                #Image.fromarray(fullImg).save(dpath31)
                Image.fromarray(subImg).save(dpath32,optimize=True,quality=30)
                tnum = tnum + 1
                #break
        #break
    return tnum

def batch(srcPath, destPath):
    
    dateDirs = os.listdir(srcPath)
    dateDirs.sort(reverse=True)
    for tdateStr in dateDirs:
        genOneDate(tdateStr)
        #break
        
if __name__ == "__main__":

    srcPath = "/data/gwac_data/gwac_orig_fits"
    destPath = "/data/gwac_data/thumbnail"
    batch(srcPath, destPath)

    
