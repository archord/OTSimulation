# -*- coding: utf-8 -*-

from astropy.io import fits
import numpy as np
import math
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

    
def fits2jpeg(spath, dpath):
    
    if not os.path.exists(dpath):
        os.system("mkdir -p %s"%(dpath))
    
    timgs = os.listdir(spath)
    for imgName in timgs:
        print(imgName)
        tpath0 = "%s/%s"%(spath, imgName)
        imgData = fits.getdata(tpath0)
        
        imgStampz = zscale_image(imgData)
        preViewPath = "%s/%s.jpg"%(dpath, imgName.split('.')[0])
        Image.fromarray(imgStampz).save(preViewPath)


if __name__ == "__main__":
    
    spath1 = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/190101_G004_041_test2_rst2/data/20191107_p1/C_align'
    dpath1 = '/home/xy/Downloads/myresource/SuperNova20190113/stampImage/190101_G004_041_test2_rst2/data/20191107_p1/I_origPreview'
    
    fits2jpeg(spath1, dpath1)