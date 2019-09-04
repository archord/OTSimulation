# -*- coding: utf-8 -*-
import numpy as np
from astropy.io import fits
import os

def saveFits(dpath, imgData):

    new_hdu = fits.PrimaryHDU(imgData)
    phdr = new_hdu.header
    phdr.set('width',imgData.shape[1])
    phdr.set('height',imgData.shape[0])
    
    new_hdu.writeto(dpath)

def batchProcess(srcPath, destPath, imgs):
    
    if not os.path.exists(destPath):
        os.makedirs(destPath)
        
    tpath1 = "%s/%s"%(srcPath, imgs)
    print("%s"%(tpath1))
    tdata1 = np.load(tpath1)
    
    totImg = tdata1['tot']
    #ts2n = tdata1['ts2n']
    
    X = totImg
    for i in range(X.shape[0]):
        if i>=10:
            break
        if i>=0:
            objPath = "%s/t%07dobj.fit"%(destPath, i)
            tmpPath = "%s/t%07dtmp.fit"%(destPath, i)
            rsiPath = "%s/t%07drsi.fit"%(destPath, i)
            tobjImg = X[i][0]
            tTempImg = X[i][1]
            tResiImg = X[i][2]
            saveFits(objPath, tobjImg)
            saveFits(tmpPath, tTempImg)
            saveFits(rsiPath, tResiImg)
            
    
    
if __name__ == "__main__":
    
    totpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_20190120"
    destPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190812'
    imgs = 'G044_mon_objt_180416T12404943_otimg_tot1245.npz'
    batchProcess(totpath, destPath, imgs)