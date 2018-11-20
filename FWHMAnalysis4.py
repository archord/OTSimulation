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

def FWHM_moffat(gamma, alpha):
    return 2*gamma * np.sqrt( 2**(1/alpha) - 1)
    
def gamma_moffat(fwhm, alpha):
    return fwhm / (2*np.sqrt( 2**(1/alpha) - 1))

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
                           alpha=3.0)
            
            fitter = fitting.LevMarLSQFitter()
            p_fit = fitter(p_init, X, Y, Z)
            Z1 = p_fit(X,Y)
            print(p_fit)
            
            print(p_fit.fwhm)
            tfwhm = FWHM_moffat(p_fit.gamma, p_fit.alpha)
            print(tfwhm)
            
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

def norm_moffat(width, power):
    from scipy.special import gamma as G
    return G(power) / (width * np.sqrt(np.pi) * G(power - 1/2))
    
def test1():
    
    from astropy.modeling.models import Moffat1D

    plt.figure()
    s1 = Moffat1D()
    r = np.arange(-5, 5, .01)
    
    for factor in range(1, 5):
        s1.gamma=4.18/factor
        s1.alpha=6.754
        print(s1.fwhm)
        #plt.plot(r, norm_moffat(s1.gamma, s1.alpha)*s1(r), color=str(0.1 * factor), lw=2)
        plt.plot(r, norm_moffat(s1.gamma, s1.alpha)*s1(r), lw=2)
    
    plt.grid()
    plt.axis([-1, 1, -0.5, 2])
    plt.show()
    
def test3():
    from astropy.modeling.functional_models import Gaussian1D
    
    def norm_gauss(sigma):
        return 1/np.sqrt(2 * np.pi * sigma**2)
    
    
    x = np.arange(-8,8,0.1)
    
    ax1 = plt.subplot(1,1,1)
    for s in range(1, 5):
        gauss  = Gaussian1D(amplitude=1, mean=0, stddev=s)    
        ax1.plot(x, norm_gauss(s)*gauss(x), ls=":", 
                 label="sigma={0:.0f}, HWHM={1:.1f}".format(s, 2.355*s/2))
        ax1.plot(x, gauss(x),label="sigma={0:.0f}, HWHM={1:.1f}".format(s, 2.355*s/2))
        
       
def test4():
    
    from astropy.modeling.models import Moffat1D

    plt.figure()
    s1 = Moffat1D()
    r = np.arange(-5, 5, .01)
    
    for fwhm in np.arange(1.8, 2.1, 0.2):
        s1.alpha=6.754
        s1.gamma=gamma_moffat(fwhm, s1.alpha)
        #print("%.3f, %.3f"%(s1.fwhm,fwhm))
        #plt.plot(r, norm_moffat(s1.gamma, s1.alpha)*s1(r), color=str(0.1 * factor), lw=2)
        plt.plot(r, norm_moffat(s1.gamma, s1.alpha)*s1(r), lw=2,
                 label='HWHM=%.3f'%(s1.fwhm))
    
    plt.grid()
    #plt.axis([-1, 1, -0.5, 2])
    plt.legend()
    plt.tight_layout()
    plt.show()
     
if __name__ == "__main__":
    
    test4()
    