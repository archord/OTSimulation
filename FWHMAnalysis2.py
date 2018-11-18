# -*- coding: utf-8 -*-
import scipy as S
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from random import randint, random
import pandas as pd
import sys
import math
import os
import time
import logging
import shutil
import scipy.ndimage
from PIL import Image
import subprocess



def fwhmrGridStatistic(catfile, size, gridNum=40):
    
    catData = np.loadtxt(catfile)
    imgW = size[0]
    imgH = size[1]
    
    tintervalW = imgW/gridNum
    tintervalH = imgH/gridNum
    print("tintervalW=%d"%(tintervalW))
    print("tintervalH=%d"%(tintervalH))
            
    tbuff = []
    for i in range(gridNum):
        for j in range(gridNum):
            tbuff.append([])
    for row in catData:
        tx = row[3]
        ty = row[4]
        xIdx = math.floor(tx/tintervalW)
        yIdx = math.floor(ty/tintervalW)
        if xIdx>= gridNum:
            xIdx = gridNum-1;
        if yIdx>= gridNum:
            yIdx = gridNum-1;
        #print("yIdx=%d,xIdx=%d"%(yIdx, xIdx))
        tIdx = yIdx * gridNum + xIdx
        tbuff[tIdx].append(row[15])
    
    fwhmMed = np.zeros((gridNum,gridNum), dtype=float)
    fwhmMin = np.zeros((gridNum,gridNum), dtype=float)
    fwhmMax = np.zeros((gridNum,gridNum), dtype=float)
        
    for i in range(gridNum):
        for j in range(gridNum):
            tIdx = i * gridNum + j
            tfwhm = np.array(tbuff[tIdx])
            if tfwhm.shape[0]==0:
                continue
            tmed = np.median(tfwhm)
            tmin = np.min(tfwhm)
            tmax = np.max(tfwhm)
            fwhmMed[i][j] = tmed
            fwhmMin[i][j] = tmin
            fwhmMax[i][j] = tmax

    x = np.arange(gridNum)
    y = np.arange(gridNum)
    X,Y = np.meshgrid(x,y)
    
    from scipy.signal import medfilt
    filterSize = 5
    Z = medfilt(fwhmMed,filterSize)
    if filterSize==5:
        Z[0][0]=Z[1][1]
        Z[0][1]=Z[1][1]
        Z[1][0]=Z[1][1]
        
        Z[0][-1]=Z[1][-2]
        Z[0][-2]=Z[1][-2]
        Z[-2][0]=Z[1][-2]
        
        Z[-1][-1]=Z[-2][-2]
        Z[-1][-2]=Z[-2][-2]
        Z[-2][-1]=Z[-2][-2]
        
        Z[-1][0]=Z[-2][1]
        Z[-1][1]=Z[-2][1]
        Z[1][-1]=Z[-2][1]
    elif filterSize==3:
        Z[0][0]=Z[1][1]
        Z[0][-1]=Z[1][-2]
        Z[-1][-1]=Z[-2][-2]
        Z[-1][0]=Z[-2][1]
    
    from mpl_toolkits.mplot3d import Axes3D
    '''
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(x, y, z, linewidth=0.2, antialiased=True)
    plt.show()
    '''
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(X,Y, Z)
    plt.show()

    
def test2():
    
    size=(4096,4136)
    #size=(3056,3056)
    osn16 = r"E:\fwhm\jfov\oi.cat" # jfov 
    fwhmrGridStatistic(osn16, size, gridNum=40)
        
        
            
if __name__ == "__main__":
    
    test2()
    