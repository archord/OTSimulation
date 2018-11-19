# -*- coding: utf-8 -*-
import scipy as S
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from random import randint, random
import pandas as pd
import math
import os
import scipy.ndimage
from PIL import Image
from astropy.stats import sigma_clip
from mpl_toolkits.mplot3d import Axes3D



def fwhmrGridStatistic(catfile, size, gridNum=40):
    
    tdata = np.loadtxt(catfile)

    maxEllipticity = 0.1
    mag = tdata[:,38]
    elpct = tdata[:,15]
    fwhm = tdata[:,18]
    
    mag1 = sigma_clip(mag, sigma=2.5, iters=3)
    minMag = np.min(mag1)
    maxMag = np.max(mag1)
    medianFwhm = np.median(fwhm)
    
    targetFwhmMax = medianFwhm
    targetMag = maxMag-6
    targetMagMin = targetMag+1
    targetMagMax = targetMag+2
    tdata = tdata[(mag>targetMagMin) & (mag<targetMagMax) & (elpct<maxEllipticity) & (fwhm<targetFwhmMax)]
    print(tdata.shape)
    
    imgData = fits.getdata(r"E:\fwhm\data1\oi.fit")
    print(imgData.shape)
    
    tRadius = 5
    for i in range(tdata.shape[1]):
        if i<10:
            trow = tdata[i]
            print("%.2f, %.2f, %.2f, %.2f, %.2f, %.2f"%(trow[3],trow[4],trow[38],trow[18],trow[15], trow[17]))
            x = int(round(trow[3]))
            y = int(round(trow[4]))
            fwhm = trow[18]
            bkg = trow[17]
            minX = x-tRadius
            maxX = x+tRadius+1
            minY = y-tRadius
            maxY = y+tRadius+1
            subImg = imgData[minY:maxY, minX:maxX]
            
            subImg = subImg - bkg
        
            x = np.arange(subImg.shape[1])
            y = np.arange(subImg.shape[0])
            X,Y = np.meshgrid(x,y)
            Z = subImg
            
            fig = plt.figure()
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.scatter(X,Y, Z)
            plt.show()
            ''' '''
            
            #https://github.com/astropy/astropy/issues/4521
            from astropy.modeling import models, fitting
            p_init = models.Moffat2D(amplitude=Z[5,5],
                           x_0=5, y_0=5,
                           gamma=fwhm,
                           alpha=1.0)
            
            fit_p = fitting.LevMarLSQFitter()
            pZ = fit_p(p_init, X, Y, Z)
            Z1 = pZ(X,Y)
            
            print(p_init.alpha)
            print(p_init.amplitude)
            print(p_init.fwhm)
            print(p_init.gamma)
            
            fig = plt.figure()
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.scatter(X,Y, Z1)
            plt.show()
            
            break


    
def test2():
    
    size=(4096,4136)
    #size=(3056,3056)
    osn16 = r"E:\fwhm\data1\oi.cat" # jfov 
    fwhmrGridStatistic(osn16, size, gridNum=40)
        
        
            
if __name__ == "__main__":
    
    test2()
    