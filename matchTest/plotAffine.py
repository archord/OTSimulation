# -*- coding: utf-8 -*-
import numpy as np
import os
import sys
import math
import time
import matplotlib.pyplot as plt
from datetime import datetime
import traceback
from matplotlib.ticker import FuncFormatter
import pandas as pd

    
def getData(srcDir, fname, destDir):
    
    ccdNum = int(fname[2:4])
    
    tdata = np.loadtxt("%s/%s"%(srcDir, fname), dtype='str')
    print(tdata.shape)
    
    fname = tdata[:,0].copy()
    dateStr = tdata[:,36].copy()
    tdata[:,0] = '0'
    tdata[:,36] = '0'
    tdata = tdata.astype(np.float)
    
    xshift,yshift, xrotation, yrotation = tdata[:,1],tdata[:,2],tdata[:,3],tdata[:,4]
    fwhmMean, bkgMean = tdata[:,38],tdata[:,40]
    tiNum, oiNum, oiJNum,tiJNum, mchNum = tdata[:,7],tdata[:,8],tdata[:,9],tdata[:,10],tdata[:,11]
    mratio0, mratio1, mratio2 = tdata[:,12],tdata[:,21],tdata[:,30]
    runTime0, runTime1, runTime2 = tdata[:,17],tdata[:,26],tdata[:,35]
    blindStarNum, featurePointNum = tdata[:,5],tdata[:,6]
    xshift0,yshift0, xrms0, yrms0 = tdata[:,13],tdata[:,14],tdata[:,15],tdata[:,16]
    xshift1,yshift1, xrms1, yrms1 = tdata[:,22],tdata[:,23],tdata[:,24],tdata[:,25]
    xshift2,yshift2, xrms2, yrms2 = tdata[:,31],tdata[:,32],tdata[:,33],tdata[:,34]
    blindMatchTime = tdata[:,-1]
    ccdNums = tdata[:,37].astype(np.int)
    
    tIdx01 = (oiNum > 4000)
    fwhmT = 3
    tIdx11 = tIdx01 & (fwhmMean<fwhmT) #fwhm=2.5,3,5;0.910174,0.950021,0.990278
    tIdx41 = tIdx11 & (featurePointNum>0)
    
    '''     '''
    #tIdx = (ccdNums==ccdNum)
    #tIdx = tIdx41 & (ccdNums==ccdNum)
    tIdx = tIdx41
    oiNum = oiNum[tIdx] 
    mratio0 = mratio0[tIdx] 
    mratio1 = mratio1[tIdx] 
    mratio2 = mratio2[tIdx] 
    print(mratio0.shape)

    return oiNum, mratio0, mratio1, mratio2
                
        
def run1():
    
    srcPath = 'data'
    destPath = "draw"
    fname1 = 'G021_mon_objt_181101T17255569_mch_statistic4000d3r4.cat'
    fname2 = 'G032_mon_objt_190110T14080401_mch_statistic4000d3r4.cat'
    fname3 = 'G043_mon_objt_190126T10594812_mch_statistic4000d3r4.cat'
    fname4 = 'G024_mon_objt_181018T18570151_mch_statistic4000d3r4.cat'
    
    if not os.path.exists(destPath):
        os.system("mkdir -p %s"%(destPath))            
    
    print("\n\n***************\nstatistic..\n")
    oiNum1, mratio01, mratio11, mratio21 = getData(srcPath, fname1, destPath)
    oiNum2, mratio02, mratio12, mratio22 = getData(srcPath, fname2, destPath)
    oiNum3, mratio03, mratio13, mratio23 = getData(srcPath, fname3, destPath)
    oiNum4, mratio04, mratio14, mratio24 = getData(srcPath, fname4, destPath)
    
    fig, axes = plt.subplots(2,2,figsize=(8,6))
    axs= axes.ravel()
    
    axs[0].plot(oiNum1, mratio21, '.', label='CCD-1')
    axs[0].grid()
    axs[0].legend(loc='lower right', framealpha=0.5)
    axs[1].plot(oiNum2, mratio22, '.', label='CCD-2')
    axs[1].grid()
    axs[1].legend(loc='lower right', framealpha=0.5)
    axs[2].plot(oiNum3, mratio23, '.', label='CCD-3')
    axs[2].grid()
    axs[2].legend(loc='lower right', framealpha=0.5)
    axs[3].plot(oiNum4, mratio24, '.', label='CCD-4')
    axs[3].grid()
    axs[3].legend(loc='lower right', framealpha=0.5)
    plt.show()
    
    fig, axes = plt.subplots(2,2,figsize=(8,6))
    axs= axes.ravel()
    
    axs[0].plot(oiNum1, mratio11, '.', label='CCD-1')
    axs[0].grid()
    axs[0].legend(loc='lower right', framealpha=0.5)
    axs[1].plot(oiNum2, mratio12, '.', label='CCD-2')
    axs[1].grid()
    axs[1].legend(loc='lower right', framealpha=0.5)
    axs[2].plot(oiNum3, mratio13, '.', label='CCD-3')
    axs[2].grid()
    axs[2].legend(loc='lower right', framealpha=0.5)
    axs[3].plot(oiNum4, mratio14, '.', label='CCD-4')
    axs[3].grid()
    axs[3].legend(loc='lower right', framealpha=0.5)
    plt.show()
    #plt.savefig('%s/DetectRatio.png'%(destPath))
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()