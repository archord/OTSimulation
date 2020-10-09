# -*- coding: utf-8 -*-

from astropy.io import fits
import numpy as np
import math
import sys
import os
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
        
    return widImg, (minx, maxx, miny, maxy)
    
def getWindowImgs(dpath1, objName, imgListFileName, size=400):
    
    dpath0 = "%s/%s"%(dpath1, objName)
    print("save image to %s"%(dpath0))
    if not os.path.exists(dpath0):
        os.system("mkdir -p %s"%(dpath0))
    
    timgs = np.loadtxt(imgListFileName, dtype='str', delimiter=',')
    for i, td in enumerate(timgs):
        
        try:
            tpath0 = td[0]
            ctrPos = (float(td[1]), float(td[2]))
            imgName = tpath0.split('/')[-1]
            print(imgName)
            
            hdulist  = fits.open(tpath0)
            hdu = hdulist[0]
            imgStamp, boundary = getWindowImg(hdu.data, ctrPos, size)
            theader = hdu.header
            hdulist.close() 
            
            CCDSEC="[%d:%d,%d:%d]" % boundary
            BIASSEC="[%d:%d,%d:%d]" % (1,boundary[1]-boundary[0]+1, 1, boundary[3]-boundary[2]+1)
            TRIMSEC=CCDSEC
            theader.set('CCDSEC',CCDSEC)
            theader.set('BIASSEC',BIASSEC)
            theader.set('TRIMSEC',TRIMSEC)
            theader.set('IMWHOLE',imgName)
            theader.set('EXTEND',False)
            theader.set('OBJECT',objName)
            
            #G191226_U000068_G043_toa_objt_191226T11021061_cut_0000.fit
            #G181212_C09598_G032_mon_objt_181212T16173898_cut_1489.fit
            newPath = "%s/%s_%s_cut_%04d.fit"%(dpath0, objName, imgName.split('.')[0], i+1)
            hdu = fits.PrimaryHDU(data=imgStamp, header=theader)
            hdul = fits.HDUList([hdu])
            hdul.writeto(newPath)
            
            imgStampz = zscale_image(imgStamp)
            preViewPath = "%s/%s_%s_cut_%04d.jpg"%(dpath0, objName, imgName.split('.')[0], i+1)
            Image.fromarray(imgStampz).save(preViewPath)
            
            if i==timgs.shape[0]-1:
                obsPath = tpath0[:22]
                timgs = os.listdir(obsPath)
                j=0
                for imgName in timgs:
                    
                    if imgName.find('dark')>-1 or imgName.find('flat')>-1:
                        #print(imgName)
                        tpath0 = "%s/%s"%(obsPath, imgName)
                        
                        hdulist  = fits.open(tpath0)
                        hdu = hdulist[0]
                        imgStamp, boundary = getWindowImg(hdu.data, ctrPos, size)
                        theader = hdu.header
                        hdulist.close() 
                        
                        CCDSEC="[%d:%d,%d:%d]" % (boundary[0],boundary[1]-1,boundary[2],boundary[3]-1)
                        BIASSEC="[%d:%d,%d:%d]" % (1,boundary[1]-boundary[0]+1, 1, boundary[3]-boundary[2]+1)
                        TRIMSEC=CCDSEC
                        theader.set('CCDSEC',CCDSEC)
                        theader.set('BIASSEC',BIASSEC)
                        theader.set('TRIMSEC',TRIMSEC)
                        theader.set('IMWHOLE',imgName)
                        theader.set('EXTEND',False)
                        theader.set('OBJECT',objName)
                        
                        #G191226_U000068_G043_toa_objt_191226T11021061_cut_0000.fit
                        #G181212_C09598_G032_mon_objt_181212T16173898_cut_1489.fit
                        newPath = "%s/%s_%s_cut_%04d.fit"%(dpath0, objName, imgName.split('.')[0], (j+i+1))
                        hdu = fits.PrimaryHDU(data=imgStamp, header=theader)
                        hdul = fits.HDUList([hdu])
                        hdul.writeto(newPath)
                        
                        imgStampz = zscale_image(imgStamp)
                        preViewPath = "%s/%s_%s_cut_%04d.jpg"%(dpath0, objName, imgName.split('.')[0], (j+i+1))
                        Image.fromarray(imgStampz).save(preViewPath)
                        
                        j=j+1

        except Exception as err:
            print(" getWindowImgs error ")
            print(err)
            
        #break

if __name__ == "__main__":
    
    dpath1 = '/data/gwac_diff_xy/cutfile'
    
    if len(sys.argv)==3:
        ObjName = sys.argv[1]
        imgListFileName = sys.argv[2]
        getWindowImgs(dpath1, ObjName, imgListFileName)
    else:
        print("/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python batchGetStampImageFromQueryResult.py ObjName imgListFileName")
        