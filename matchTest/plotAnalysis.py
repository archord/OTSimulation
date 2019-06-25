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

def aa():
    
        fname1 = 'G021_mon_objt_181101T17255569_mch_statistic.cat'
        fname2 = 'G032_mon_objt_190110T14080401_mch_statistic.cat'
        fname3 = 'G043_mon_objt_190126T10594812_mch_statistic.cat'
        fname4 = 'G024_mon_objt_181018T18570151_mch_statistic.cat'
        
        tdata1 = np.loadtxt("%s/%s"%(srcDir, fname1), dtype='str')
        print(tdata1.shape)
        tdata2 = np.loadtxt("%s/%s"%(srcDir, fname2), dtype='str')
        print(tdata2.shape)
        tdata3 = np.loadtxt("%s/%s"%(srcDir, fname3), dtype='str')
        print(tdata3.shape)
        tdata4 = np.loadtxt("%s/%s"%(srcDir, fname4), dtype='str')
        print(tdata4.shape)
        
        tdata = np.concatenate([tdata1,tdata2,tdata3,tdata4])
        print(tdata.shape)
    
    
def magStatistic1(srcDir, fname, destDir):
    
    try:
        print(fname)
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
                
        print(tiNum)
        plt.plot(oiNum,mratio0, '.')
        plt.show()
        plt.plot(oiNum,mratio1, '.')
        plt.show()
        plt.plot(oiNum,mratio2, '.')
        plt.show()
        
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        
def run1():
    
    srcPath = 'data'
    destPath = "draw"
    fname1 = 'G021_mon_objt_181101T17255569_mch_statistic.cat'
    fname2 = 'G032_mon_objt_190110T14080401_mch_statistic.cat'
    fname3 = 'G043_mon_objt_190126T10594812_mch_statistic.cat'
    fname4 = 'G024_mon_objt_181018T18570151_mch_statistic.cat'
    
    if not os.path.exists(destPath):
        os.system("mkdir -p %s"%(destPath))            
    
    print("\n\n***************\nstatistic..\n")
    magStatistic1(srcPath, fname1, destPath)
    magStatistic1(srcPath, fname2, destPath)
    magStatistic1(srcPath, fname3, destPath)
    magStatistic1(srcPath, fname4, destPath)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()