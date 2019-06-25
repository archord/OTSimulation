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

def unionStatistic2():
    
    srcDir = 'data'
    fname1 = 'G021_mon_objt_181101T17255569_mch_statistic4000.cat'
    fname2 = 'G032_mon_objt_190110T14080401_mch_statistic4000.cat'
    fname3 = 'G043_mon_objt_190126T10594812_mch_statistic4000.cat'
    fname4 = 'G024_mon_objt_181018T18570151_mch_statistic4000.cat'
    
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
    
    fname = tdata[:,0].copy()
    dateStr = tdata[:,36].copy()
    tdata[:,0] = '0'
    tdata[:,36] = '0'
    tdata = tdata.astype(np.float)
    
    blindStarNum, featurePointNum = tdata[:,5],tdata[:,6]
    mratio0, mratio1, mratio2 = tdata[:,12],tdata[:,21],tdata[:,30]
    fwhmMean, bkgMean = tdata[:,38],tdata[:,40]
    tiNum, oiNum, oiJNum,tiJNum, mchNum = tdata[:,7],tdata[:,8],tdata[:,9],tdata[:,10],tdata[:,11]
    tIdx = (blindStarNum>0) & (featurePointNum>0) & (mratio2>80)
    tdata80 = tdata[tIdx]
    print(tdata80.shape)
    tIdx = (blindStarNum>0) & (featurePointNum>0) & (mratio2>=60)
    tdata = tdata[tIdx]
    print(tdata.shape)
    
    xshift,yshift, xrotation, yrotation = tdata[:,1],tdata[:,2],tdata[:,3],tdata[:,4]
    fwhmMean, bkgMean = tdata[:,38],tdata[:,40]
    tiNum, oiNum, oiJNum,tiJNum, mchNum = tdata[:,7],tdata[:,8],tdata[:,9],tdata[:,10],tdata[:,11]
    mratio0, mratio1, mratio2 = tdata[:,12],tdata[:,21],tdata[:,30]
    runTime0, runTime1, runTime2 = tdata[:,17],tdata[:,26],tdata[:,35]
    blindStarNum, featurePointNum = tdata[:,5],tdata[:,6]
    xshift0,yshift0, xrms0, yrms0 = tdata[:,13],tdata[:,14],tdata[:,15],tdata[:,16]
    xshift1,yshift1, xrms1, yrms1 = tdata[:,22],tdata[:,23],tdata[:,24],tdata[:,25]
    xshift2,yshift2, xrms2, yrms2 = tdata[:,31],tdata[:,32],tdata[:,33],tdata[:,34]
    blindMchTime = tdata[:,-1]
    '''
    plt.hist(mchNum,20)
    plt.title("mchNum")
    plt.grid()
    plt.show()
    
    plt.hist(mratio2,20)
    plt.title("mratio2")
    plt.grid()
    plt.show()
    
    plt.hist(blindMchTime,20)
    plt.title("blindMchTime")
    plt.grid()
    plt.show()
    
    plt.hist(xshift,20)
    plt.title("xshift")
    plt.grid()
    plt.show()
    
    plt.hist(xshift2,20)
    plt.title("xshift2")
    plt.grid()
    plt.show()
    
    plt.hist(yshift,20)
    plt.title("yshift")
    plt.grid()
    plt.show()
    
    plt.hist(yshift2,20)
    plt.title("yshift2")
    plt.grid()
    plt.show()
    
    plt.hist(xrotation,20)
    plt.title("rotation")
    plt.grid()
    plt.show()

    plt.hist(xrms2,20)
    plt.title("xrms2")
    plt.grid()
    plt.show()
    
    plt.hist(yrms2,20)
    plt.title("yrms2")
    plt.grid()
    plt.show()
    '''
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
        
def unionStatistic(tnum=4000):
    
    srcDir = 'data'
    fname1 = 'G021_mon_objt_181101T17255569_mch_statistic%d.cat'%(tnum)
    fname2 = 'G032_mon_objt_190110T14080401_mch_statistic%d.cat'%(tnum)
    fname3 = 'G043_mon_objt_190126T10594812_mch_statistic%d.cat'%(tnum)
    fname4 = 'G024_mon_objt_181018T18570151_mch_statistic%d.cat'%(tnum)
    
    tdata1 = np.loadtxt("%s/%s"%(srcDir, fname1), dtype='str')
    tdata2 = np.loadtxt("%s/%s"%(srcDir, fname2), dtype='str')
    tdata3 = np.loadtxt("%s/%s"%(srcDir, fname3), dtype='str')
    tdata4 = np.loadtxt("%s/%s"%(srcDir, fname4), dtype='str')
    
    tdata = np.concatenate([tdata1,tdata2,tdata3,tdata4])
    totalFileNum = tdata.shape[0]
    
    fname = tdata[:,0].copy()
    dateStr = tdata[:,36].copy()
    tdata[:,0] = '0'
    tdata[:,36] = '0'
    tdata = tdata.astype(np.float)
    
    blindStarNum, featurePointNum = tdata[:,5],tdata[:,6]
    mratio0, mratio1, mratio2 = tdata[:,12],tdata[:,21],tdata[:,30]
    fwhmMean, bkgMean = tdata[:,38],tdata[:,40]
    tiNum, oiNum, oiJNum,tiJNum, mchNum = tdata[:,7],tdata[:,8],tdata[:,9],tdata[:,10],tdata[:,11]
    xshift,yshift, xrotation, yrotation = tdata[:,1],tdata[:,2],tdata[:,3],tdata[:,4]
    
    
    print(totalFileNum)
    tIdx01 = (oiNum > 4000)
    tIdx02 = (oiNum > 0.8*tiNum)
    oiImgNum1 = np.sum(tIdx01)
    oiImgNum2 = np.sum(tIdx02)
    print("%d,%.2f;%d,%.2f"%(oiImgNum1,oiImgNum1*100.0/totalFileNum,oiImgNum2,oiImgNum2*100.0/totalFileNum))

    fwhmT = 3
    tIdx11 = tIdx01 & (fwhmMean<fwhmT) #fwhm=2.5,3,5;0.910174,0.950021,0.990278
    tIdx12 = tIdx02 & (fwhmMean<fwhmT) #fwhm=2.5,3,5;0.910174,0.950021,0.990278
    goodImgNum1 = np.sum(tIdx11)
    goodImgNum2 = np.sum(tIdx12)
    print("%d,%.2f;%d,%.2f"%(goodImgNum1,goodImgNum1*100.0/totalFileNum,goodImgNum2,goodImgNum2*100.0/totalFileNum))

    mratioT = 70
    tIdx21 = tIdx11 & (mratio2>mratioT)
    tIdx22 = tIdx12 & (mratio2>mratioT)
    goodMatch1 = np.sum(tIdx21)
    goodMatch2 = np.sum(tIdx22)
    print("%d,%.2f;%d,%.2f"%(goodMatch1,goodMatch1*100.0/goodImgNum1,goodMatch2,goodMatch2*100.0/goodImgNum2))
    
    mratioT = 70
    tIdx31 = tIdx11 & (mratio2<mratioT)
    tIdx32 = tIdx12 & (mratio2<mratioT)

    xshift = xshift[tIdx21]
    yshift = yshift[tIdx21]
    mratio2 = mratio2[tIdx21]
    
    ''' '''
    plt.plot(xshift, mratio2,'.')
    plt.title("mchNum1")
    plt.grid()
    plt.show()
    
    plt.plot(yshift, mratio2,'.')
    plt.title("mchNum2")
    plt.grid()
    plt.show()
    
def run1():
    
    srcPath = 'data'
    destPath = "draw"
    fname1 = 'G021_mon_objt_181101T17255569_mch_statistic2.cat'
    fname2 = 'G032_mon_objt_190110T14080401_mch_statistic2.cat'
    fname3 = 'G043_mon_objt_190126T10594812_mch_statistic2.cat'
    fname4 = 'G024_mon_objt_181018T18570151_mch_statistic2.cat'
    
    if not os.path.exists(destPath):
        os.system("mkdir -p %s"%(destPath))            
    
    print("\n\n***************\nstatistic..\n")
    magStatistic1(srcPath, fname1, destPath)
    #magStatistic1(srcPath, fname2, destPath)
    #magStatistic1(srcPath, fname3, destPath)
    #magStatistic1(srcPath, fname4, destPath)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    #run1()
    unionStatistic(4000)
    #unionStatistic(8000)