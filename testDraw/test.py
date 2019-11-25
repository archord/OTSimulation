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
    
    tpath = r'e:\poserr2.log'
    tf = open(tpath, 'r')
    
    parms = []
    for tline in tf.readlines():
        td = tline[30:-2]
        parm = td.split(',')
        parms.append(parm[:-3])

    tf.close()
    
    parms = np.array(parms).astype(np.float)
    print(parms.shape)
    
    tIdx = (parms[:,-1]>0.5) | (parms[:,-2]>0.5)
    #tIdx = parms[:,0]>0
    tnum = parms[tIdx,-2]
    tperct = parms[tIdx,-1]
    
    plt.figure(figsize=(10,4))
    plt.plot(tnum, tperct, '.')
    plt.show()
    
    tnum = parms[tIdx,6]
    plt.figure(figsize=(10,4))
    n, bins, patches =plt.hist(tnum, bins=10, rwidth=0.8)
    plt.show()

if __name__ == "__main__":
        
    draw2()