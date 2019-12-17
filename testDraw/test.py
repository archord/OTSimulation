# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage
import math
from PIL import Image
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA

    
def draw3():
    
    tpath = r'e:\poserr.log'
    tf = open(tpath, 'r')
    
    parms = []
    for tline in tf.readlines():
        td = tline[30:-2]
        parm = td.split(',')
        parms.append(parm)

    tf.close()
    
    parms = np.array(parms).astype(np.float)
    print(parms.shape)
    
    
    thNum = 5
    tnum = parms[:,0]
    tnum0 = tnum[tnum>thNum]
    print("num>%d=%f"%(thNum, tnum0.shape[0]/tnum.shape[0]))
    
    thNum = 10
    tnum0 = tnum[tnum>thNum]
    print("num>%d=%f"%(thNum, tnum0.shape[0]/tnum.shape[0]))
    
    thNum = 15
    tnum0 = tnum[tnum>thNum]
    print("num>%d=%f"%(thNum, tnum0.shape[0]/tnum.shape[0]))
    
    thNum = 20
    tnum0 = tnum[tnum>thNum]
    print("num>%d=%f"%(thNum, tnum0.shape[0]/tnum.shape[0]))
    
    thNum = 0.3*100
    tnum = parms[:,-1]
    tnum0 = tnum[tnum>thNum]
    print("percent>%f=%f"%(thNum, tnum0.shape[0]/tnum.shape[0]))
    
    thNum = 0.5*100
    tnum0 = tnum[tnum>thNum]
    print("percent>%f=%f"%(thNum, tnum0.shape[0]/tnum.shape[0]))
    
    thNum = 0.7*100
    tnum0 = tnum[tnum>thNum]
    print("percent>%f=%f"%(thNum, tnum0.shape[0]/tnum.shape[0]))
    
    thNum = 0.8*100
    tnum0 = tnum[tnum>thNum]
    print("percent>%f=%f"%(thNum, tnum0.shape[0]/tnum.shape[0]))
    
    tIdx = parms[:,-1]<90
    tnum = parms[tIdx,0]
    tnum = tnum[tnum<9]
    print(tnum.shape)
    plt.figure(figsize=(10,4))
    n, bins, patches =plt.hist(tnum, bins=10, rwidth=0.8)
    #tbins = np.linspace(0, 100, 11)
    #tbins = np.linspace(0, 100, 11)
    #plt.xticks(tbins)
    plt.show()
    
    
def draw2():
    
    tpath = r'e:\poserr4.log'
    tf = open(tpath, 'r')
    
    parms = []
    for tline in tf.readlines():
        td = tline[30:-2]
        parm = td.split(',')
        parms.append(parm[:-3])

    tf.close()
    
    parms = np.array(parms).astype(np.float)
    print(parms.shape)
    
    #tIdx = (parms[:,-1]>0.3) | (parms[:,-2]>0.3)
    #tIdx = parms[:,6]>80
    tIdx = (parms[:,0]>=3) & (parms[:,0]<5)
    tnum = parms[tIdx,-2]
    tperct = parms[tIdx,-1]
    
    plt.figure(figsize=(10,4))
    plt.plot(tnum, tperct, '.')
    plt.show()
    '''    
    tnum = parms[tIdx,0]
    plt.figure(figsize=(10,4))
    n, bins, patches =plt.hist(tnum, bins=10, rwidth=0.8)
    plt.show()
    '''
    
def getGreatCircleDistance(ra1, dec1, ra2, dec2):
    rst = 57.295779513 * np.arccos(np.sin(0.017453293 * dec1) * np.sin(0.017453293 * dec2)
        + np.cos(0.017453293 * dec1) * np.cos(0.017453293 * dec2) * np.cos(0.017453293 * (np.abs(ra1 - ra2))));
    return rst
  
def draw4():
    
    from mpl_toolkits.mplot3d import Axes3D
    from astropy.coordinates import SkyCoord 
    #%matplotlib inline
    
    tpath = r'e:\final.cat.astro.qiuyl'
    parms = np.loadtxt(tpath)
    print(parms.shape)
    
    tIdx = np.random.choice(parms.shape[0], int(parms.shape[0]*0.01), replace=False)
    parms = parms[tIdx].copy()
    
    ra1= parms[:,0]
    dec1= parms[:,1]
    ra2= parms[:,-2]
    dec2= parms[:,-1]
    x= parms[:,2]
    y= parms[:,3]
    
    dist0= getGreatCircleDistance(ra1, dec1, ra2, dec2)
    
    c1 = SkyCoord(ra1, dec1, unit="deg")
    c2 = SkyCoord(ra2, dec2, unit="deg")
    dist = c1.separation(c2)
    print(dist.shape)
    print(np.max(np.abs(dist.degree-dist0)))
    
    #dec0 = np.abs(dec1-dec2)
    #ra0 = np.abs(ra1-ra2)/np.cos(np.deg2rad(dec0))
    dec0 = dec1-dec2
    ra0 = (ra1-ra2)/np.cos(np.deg2rad(dec0))
    
    fig = plt.figure(figsize=(10,4))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(x, y, dist0, '.')
    plt.show()
    '''    
    tnum = parms[tIdx,0]
    plt.figure(figsize=(10,4))
    n, bins, patches =plt.hist(tnum, bins=10, rwidth=0.8)
    plt.show()
    '''

    
if __name__ == "__main__":
        
    draw4()