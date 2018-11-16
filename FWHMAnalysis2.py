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



def fwhmrGridStatistic(catfile, gridNum=100):
    
    catData = np.loadtxt(catfile)
    imgW = 3056 #jfov:3056
    imgH = 3056
    
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
        xIdx = math.floor(tx%tintervalW)
        yIdx = math.floor(ty%tintervalW)
        tIdx = yIdx * gridNum + xIdx
        tbuff[tIdx].append(row[19])
    
    fwhmMed = np.zeros((gridNum,gridNum), dtype=float)
    fwhmMin = np.zeros((gridNum,gridNum), dtype=float)
    fwhmMax = np.zeros((gridNum,gridNum), dtype=float)
    
    x = []
    y = []
    z = []
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
            x.append(j)
            y.append(i)
            z.append(tmed)
    
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(x, y, z, linewidth=0.2, antialiased=True)
    plt.show()

    
def test2():
    
    osn16 = r"E:\fwhm\jfov\oi_sn16.cat"
    fwhmrGridStatistic(osn16, gridNum=100)
        
        
            
if __name__ == "__main__":
    
    test2()
    