# -*- coding: utf-8 -*-

from astropy.io import fits
import numpy as np
import math
import os
import scipy.ndimage
from PIL import Image

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
    
def getWindowImgs(spath, dpath, ctrPos, size=100):
    
    if not os.path.exists(dpath):
        os.system("mkdir -p %s"%(dpath))
    
    timgs = os.listdir(spath)
    for imgName in timgs:
        if len(imgName)!=len("G041_mon_objt_190101T20584991_s800_conv_cmb356.fit"):
            continue
        print(imgName)
        tpath0 = "%s/%s"%(spath, imgName)
        imgData = fits.getdata(tpath0)
        imgStamp = getWindowImg(imgData, ctrPos, size)
        
        newPath = "%s/%s_s%d.fit"%(dpath, imgName.split('.')[0], size)
        hdu = fits.PrimaryHDU(imgStamp)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath)
        
        zoom=3
        objData = scipy.ndimage.zoom(imgStamp, zoom, order=0)
        
        newPath = "%s/%s_zoom%d.fit"%(spath, imgName.split('.')[0], zoom)
        hdu = fits.PrimaryHDU(objData)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath)


if __name__ == "__main__":
    
    spath1 = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/cmb_rst/data/20191107_p1/C_align'
    dpath1 = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/cmb_rst/data/20191107_p1/C_align'
    
    ctrPos=(400,400)
    size=600
    getWindowImgs(spath1, dpath1, ctrPos, size)