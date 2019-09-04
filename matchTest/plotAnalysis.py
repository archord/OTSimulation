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
    fname1 = 'G021_mon_objt_181101T17255569_mch_statistic%dd3r4.cat'%(tnum)
    fname2 = 'G032_mon_objt_190110T14080401_mch_statistic%dd3r4.cat'%(tnum)
    fname3 = 'G043_mon_objt_190126T10594812_mch_statistic%dd3r4.cat'%(tnum)
    fname4 = 'G024_mon_objt_181018T18570151_mch_statistic%dd3r4.cat'%(tnum)
    
    tdata1 = np.loadtxt("%s/%s"%(srcDir, fname1), dtype='str')
    tdata2 = np.loadtxt("%s/%s"%(srcDir, fname2), dtype='str')
    tdata3 = np.loadtxt("%s/%s"%(srcDir, fname3), dtype='str')
    tdata4 = np.loadtxt("%s/%s"%(srcDir, fname4), dtype='str')
    #print(tdata1[0,7])
    #print(tdata2[0,7])
    #print(tdata3[0,7])
    #print(tdata4[0,7])
    
    tdata = np.concatenate([tdata1,tdata2,tdata3,tdata4])
    totalFileNum = tdata.shape[0]
    
    #aa=tdata[tdata[:,0]=='G044_mon_objt_190201T12292341.cat'][0]
    #print(np.abs(aa[[1,2,3,8,38]].astype(np.float)))
    #print(aa[1],aa[2],aa[3],aa[38],aa[8],aa[11],aa[30])
    #return
    
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
    xshift3,yshift3, xrms3, yrms3 = tdata[:,47],tdata[:,48],tdata[:,49],tdata[:,50]
    blindMatchTime = tdata[:,42]
    ccdNums = tdata[:,37].astype(np.int)
    
    
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

    tIdx41 = tIdx11 & (featurePointNum>0)
    tIdx42 = tIdx12 & (featurePointNum>0)
    tIdx51 = tIdx11 & (featurePointNum==0)
    tIdx52 = tIdx12 & (featurePointNum==0)
    errorMatch1 = np.sum(tIdx51)
    errorMatch2 = np.sum(tIdx52)
    #print(fname[tIdx51])
    #print(fname[tIdx52])
    print("errorMatch1=%d"%(errorMatch1))
    print("errorMatch2=%d"%(errorMatch2))
    
    mratioT = 70
    tIdx21 = tIdx11 & (mratio2>=mratioT) & (featurePointNum>0)
    tIdx22 = tIdx12 & (mratio2>=mratioT) & (featurePointNum>0)
    goodMatch1 = np.sum(tIdx21)
    goodMatch2 = np.sum(tIdx22)
    print("%d,%.2f;%d,%.2f"%(goodMatch1,goodMatch1*100.0/goodImgNum1,goodMatch2,goodMatch2*100.0/goodImgNum2))
        
    tIdx31 = tIdx11 & (mratio2<mratioT) & (featurePointNum>0)
    tIdx32 = tIdx12 & (mratio2<mratioT) & (featurePointNum>0)
    badMatch1 = np.sum(tIdx31)
    badMatch2 = np.sum(tIdx32)
    print("badMatch1=%d"%(badMatch1))
    if badMatch1>0:
        print(fname[tIdx31])
        print(xshift[tIdx31])
        print(yshift[tIdx31])
        print(xrotation[tIdx31])
        print(fwhmMean[tIdx31])
        print(oiNum[tIdx31])
        print(mratio2[tIdx31])
        print("badMatch2=%d"%(badMatch2))
        print("%d,%.2f;%d,%.2f"%(badMatch1,badMatch1*100.0/goodImgNum1,badMatch2,badMatch2*100.0/goodImgNum2))
        #print(fname[tIdx32])
        
        featurePointNum1 = featurePointNum[tIdx31]
        featurePointNum2 = featurePointNum[tIdx32]
        blindStarNum1 = blindStarNum[tIdx21]
        blindStarNum2 = blindStarNum[tIdx22]
        print(np.min(featurePointNum1))
        print(np.min(featurePointNum2))
        print(np.min(blindStarNum1))
        print(np.min(blindStarNum2))
    
    #mratio2 = mchNum/oiNum
    oiNum1 = oiNum[tIdx41]
    mratio21 = mratio2[tIdx41]
    mratio21[mratio21>100]=100
    print(np.max(mratio21))
    
    plt.plot(oiNum1, mratio21, '.')
    plt.title("StarNum -- matchRatio")
    plt.grid()
    plt.show()
    
    xrms21 = xrms2[tIdx41]
    plt.hist(xrms21, 20)
    plt.title("XRMS order 3, avg=%.4f"%(np.average(xrms21)))
    plt.grid()
    plt.show()
    
    yrms21 = yrms2[tIdx41]
    plt.hist(yrms21, 20)
    plt.title("YRMS order 3, avg=%.4f"%(np.average(yrms21)))
    plt.grid()
    plt.show()
    
    xrms21 = xrms3[tIdx41]
    plt.hist(xrms21, 20)
    plt.title("XRMS order 5, avg=%.4f"%(np.average(xrms21)))
    plt.grid()
    plt.show()
    
    yrms21 = yrms3[tIdx41]
    plt.hist(yrms21, 20)
    plt.title("YRMS order 5, avg=%.4f"%(np.average(yrms21)))
    plt.grid()
    plt.show()
    
    
    xrms21 = xshift2[tIdx41]
    plt.hist(xrms21, 40)
    plt.title("xshift order 3, avg=%.4f"%(np.average(xrms21)))
    plt.grid()
    plt.show()
    
    yrms21 = yshift2[tIdx41]
    plt.hist(yrms21, 40)
    plt.title("yshift order 3, avg=%.4f"%(np.average(yrms21)))
    plt.grid()
    plt.show()
    
    xrms21 = xshift3[tIdx41]
    plt.hist(xrms21, 40)
    plt.title("xshift order 5, avg=%.4f"%(np.average(xrms21)))
    plt.grid()
    plt.show()
    
    yrms21 = yshift3[tIdx41]
    plt.hist(yrms21, 40)
    plt.title("yshift order 5, avg=%.4f"%(np.average(yrms21)))
    plt.grid()
    plt.show()
    
    blindMatchTime1 = blindMatchTime[tIdx41]
    plt.hist(blindMatchTime1, 20)
    plt.title("blindMatchTime, avg=%.0fms"%(np.average(blindMatchTime1)))
    plt.grid()
    plt.show()
    
    xshift = xshift[tIdx41] #xshift,yshift, xrotation
    plt.hist(xshift, 20)
    plt.title("xshift")
    plt.grid()
    plt.show()
    
    yshift = yshift[tIdx41] #xshift,yshift, xrotation
    plt.hist(yshift, 20)
    plt.title("yshift")
    plt.grid()
    plt.show()
    
    xrotation = xrotation[tIdx41] #xshift,yshift, xrotation
    plt.hist(xrotation, 20)
    plt.title("rotation")
    plt.grid()
    plt.show()
    
    tshift = np.sqrt(xshift*xshift + yshift*yshift)
    plt.hist(tshift, 20)
    plt.title("tshift")
    plt.grid()
    plt.show()
    
    totalNum = tshift.shape[0]
    num100 = tshift[tshift>100].shape[0]
    num400 = tshift[tshift>400].shape[0]
    num1000 = tshift[tshift>1000].shape[0]
    print([num100/totalNum,num400/totalNum,num1000/totalNum])
    
    xrotation = np.abs(xrotation)
    totalNum = xrotation.shape[0]
    num1 = xrotation[xrotation>1].shape[0]
    num5 = xrotation[xrotation>5].shape[0]
    print([num1/totalNum,num5/totalNum])
    
    
    ''' 
    oiNum2 = oiNum[tIdx42]
    mratio22 = mratio2[tIdx42]
    plt.plot(oiNum2, mratio22, '.')
    plt.title("StarNum -- matchRatio")
    plt.grid()
    plt.show()
    '''
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