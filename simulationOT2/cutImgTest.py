# -*- coding: utf-8 -*-

from astropy.io import fits
import numpy as np
import math
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

def getWindowImg(img, ctrPos, size=100):
    
    imgSize = img.shape
    hsize = int(size/2)
    tpad = int(size%2)
    ctrX = math.ceil(ctrPos[0])
    ctrY = math.ceil(ctrPos[1])
    
    minx = ctrX - hsize
    maxx = ctrX + hsize + tpad
    miny = ctrY - hsize
    maxy = ctrY + hsize + tpad
    
    widImg = []
    if minx>0 and miny>0 and maxx<imgSize[1] and maxy<imgSize[0]:
        widImg=img[miny:maxy,minx:maxx]
        
    return widImg
    
def getWindowImgs(tpath, objImg, objCat, size=100):
    
    objPath = "%s/%s"%(objImg)
    objData = fits.getdata(objPath)
    
    tdata1 = np.loadtxt("%s/%s"%(tpath, objCat))
    poslist = tdata1[:,0:2] #x,y
    
    subImgs = []
    for tpos in poslist:
        objWid = getWindowImg(objData, (tpos[0], tpos[1]), size)
        subImgs.append(objWid)
            
    return subImgs


if __name__ == "__main__":
    
    tpath = '/home/gwac'
    objImg = 'objImg.fit'
    objCat = 'objImg.cat'
    
    subImgs = getWindowImgs(tpath, objImg, objCat)
    
    for i, timg in enumerate(subImgs):
        tdata1 = zscale_image(timg)
        preViewPath = "%s/%s_%04d.jpg"%(tpath, objImg.split('.'))
        Image.fromarray(timg).save(preViewPath)