# -*- coding: utf-8 -*-
import os
from astropy.stats import sigma_clip
import numpy as np
import scipy.ndimage
import math
from astropy.io import fits
import traceback
import cv2
import traceback
from datetime import datetime
import scipy.ndimage
from PIL import Image


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

def getWindowImg(img, ctrPos, size):
    
    imgSize = img.shape
    hsize = int(size/2)
    tpad = int(size%2)
    ctrX = math.ceil(ctrPos[0])
    ctrY = math.ceil(ctrPos[1])
    
    minx = int(ctrX - hsize)
    maxx = int(ctrX + hsize + tpad)
    miny = int(ctrY - hsize)
    maxy = int(ctrY + hsize + tpad)
    
    widImg = []
    if minx>0 and miny>0 and maxx<imgSize[1] and maxy<imgSize[0]:
        widImg=img[miny:maxy,minx:maxx]
        
    return widImg

def getWindowImgs(srcDir, objImg, tmpImg, resiImg, catData, size):
    
    objPath = "%s/%s"%(srcDir, objImg)
    tmpPath = "%s/%s"%(srcDir, tmpImg)
    resiPath = "%s/%s"%(srcDir, resiImg)
    
    objData = fits.getdata(objPath)
    tmpData = fits.getdata(tmpPath)
    resiData = fits.getdata(resiPath)
    
    subImgs = []
    parms = []
    for td in catData:
        try:
            objWid = getWindowImg(objData, (td[0], td[1]), size)
            tmpWid = getWindowImg(tmpData, (td[0], td[1]), size)
            resiWid = getWindowImg(resiData, (td[0], td[1]), size)
            
            if len(objWid)>0 and len(tmpWid)>0 and len(resiWid)>0:
                subImgs.append([objWid, tmpWid, resiWid])
                parms.append(td)
                
        except Exception as e:
            tstr = traceback.format_exc()
            print(tstr)
            
    return np.array(subImgs), np.array(parms)

def getStampImages(fullImgPath, newImg, tmpImg, resImg, objCat):
    
    nameBase = newImg[:newImg.index(".")]
            
    catData = np.load("%s/%s"%(fullImgPath, objCat))
    
    tSubImgs = getWindowImgs(fullImgPath, newImg, tmpImg, resImg, catData, 100)
    
    i=1
    for timg in tSubImgs:
        objWid, tmpWid, resiWid = timg[0],timg[1],timg[2]
        
        objWidz = zscale_image(objWid)
        tmpWidz = zscale_image(tmpWid)
        resiWidz = zscale_image(resiWid)
        objWidz = scipy.ndimage.zoom(objWidz, 2, order=0)
        tmpWidz = scipy.ndimage.zoom(tmpWidz, 2, order=0)
        resiWidz = scipy.ndimage.zoom(resiWidz, 2, order=0)
        
        objWidz = objWidz.reshape(objWidz.shape[0], objWidz.shape[1],1).repeat(3,2)
        tmpWidz = tmpWidz.reshape(tmpWidz.shape[0], tmpWidz.shape[1],1).repeat(3,2)
        resiWidz = resiWidz.reshape(resiWidz.shape[0], resiWidz.shape[1],1).repeat(3,2)
        
        shift00=3
        cv2.circle(objWidz, (int(objWidz.shape[0]/2)-shift00, int(objWidz.shape[1]/2)-shift00), 10, (0,255,0), thickness=2)
        cv2.circle(tmpWidz, (int(tmpWidz.shape[0]/2)-shift00, int(tmpWidz.shape[1]/2)-shift00), 10, (0,255,0), thickness=2)
        cv2.circle(resiWidz, (int(resiWidz.shape[0]/2)-shift00, int(resiWidz.shape[1]/2)-shift00), 10, (0,255,0), thickness=2)
        
        spaceLine = np.ones((objWidz.shape[0],5), dtype=np.uint8)*255
        spaceLine = spaceLine.reshape(spaceLine.shape[0], spaceLine.shape[1],1).repeat(3,2)
        sub2Con = np.concatenate((objWidz, spaceLine, tmpWidz, spaceLine, resiWidz), axis=1)
        
        tImgName = "%s_%05d.jpg"%(nameBase,i)
        savePath = "%s/%s"%(fullImgPath, tImgName)
        Image.fromarray(sub2Con).save(savePath)
        i = i+1
        
if __name__ == "__main__":
    
    fullImgPath = '' 
    newImg = '' 
    tmpImg = '' 
    resImg = '' 
    objCat = ''
    
    getStampImages(fullImgPath, newImg, tmpImg, resImg, objCat)