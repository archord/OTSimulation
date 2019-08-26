# -*- coding: utf-8 -*-
import numpy as np
from astropy.io import fits
import traceback
import os

def saveFits(dpath, imgData):

    new_hdu = fits.PrimaryHDU(imgData)
    phdr = new_hdu.header
    phdr.set('width',imgData.shape[1])
    phdr.set('height',imgData.shape[0])
    
    new_hdu.writeto(dpath)

def getFits(destPath):
    
    if not os.path.exists(destPath):
        os.makedirs(destPath)
        
    #tpath1 = '/home/xy/Downloads/myresource/deep_data2/simot/train_20190122/SIM_TOT_REAL_FOT_bin_none_64_fot10w_20190122.npz'
    tpath1 = '/home/xy/Downloads/myresource/deep_data2/simot/train_20190122/FINAL_TEST_ADD_REAL_DATA_bin_none.npz'
    print("%s"%(tpath1))
    tdata1 = np.load(tpath1)
    X = tdata1['X']
    Y = tdata1['Y']
    s2n = tdata1['s2n']
    print(X.shape)
    print(Y.shape)
    
    for i in range(X.shape[0]):

        try:
            if i%10==1:
                print(i)
            destPath1 = "%s/%d"%(destPath,Y[i][1])
            objPath = "%s/t%07dobj.fit"%(destPath1, i)
            tmpPath = "%s/t%07dtmp.fit"%(destPath1, i)
            rsiPath = "%s/t%07drsi.fit"%(destPath1, i)
            tobjImg = X[i][0]
            tTempImg = X[i][1]
            tResiImg = X[i][2]
            saveFits(objPath, tobjImg)
            saveFits(tmpPath, tTempImg)
            saveFits(rsiPath, tResiImg)
            
        except Exception as e:
            print(e)
            tstr = traceback.format_exc()
            print(tstr)
    
if __name__ == "__main__":
    
    totpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_20190120"
    #destPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190812/fit'
    destPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190812/fit2'
    imgs = 'G044_mon_objt_180416T12404943_otimg_tot1245.npz'
    getFits(destPath)
    