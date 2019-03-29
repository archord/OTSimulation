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

        
def getAllData(srcFitDir, start, end):
    
    try:
            
        tfiles0 = os.listdir(srcFitDir)
        tfiles0.sort()
        
        tfiles = []
        for tfile in tfiles0:
            if len(tfile)==len('G031_mon_objt_190116T20334726_cmb005.cat'):
                tfiles.append(tfile)
        
        totalNum = len(tfiles)        
        starAll = np.array([])
        
        tnum = 0
        for i in range(totalNum):
            
            if i<start or i>end:
                continue
            
            imgName = tfiles[i]
            imgpre= imgName.split(".")[0]
            tname1 = "%s/%s_starmch.cat"%(srcFitDir,imgpre)
            
            starmch = np.loadtxt(tname1)
            starmchMag = starmch[:,2]
            
            if starmchMag.shape[0]>1:
                if starAll.shape[0]==0:
                    starAll = starmchMag
                else:
                    starAll=np.concatenate((starAll, starmchMag), axis =0)
                tnum += 1
                
        return starAll, tnum
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        return np.array([]), 0

def binCount(tdata, minD=16.0, maxD=18.0, binNum=10):
    
    binInter = (maxD-minD)/binNum
    magCount1 = np.zeros(10)
    
    for tmag in tdata:
        tIdx = int((tmag - minD)/binInter)
        if tIdx>binNum-1:
            tIdx=binNum-1
        if tIdx<0:
            tIdx=0
        magCount1[tIdx] = magCount1[tIdx] +1
    
    return magCount1


def magStatistic1(srcDir, destDir):
    
    try:
    
        binNum = 10
        tbins = np.linspace(16.1, 17.9, binNum)
        
        fig, axes = plt.subplots(1,2,figsize=(16,6))
        axs= axes.ravel()
        
        d005 = "%s/3/005"%(srcDir)
        d025 = "%s/3/025"%(srcDir)
        d125 = "%s/3/125"%(srcDir)
        d200 = "%s/3/200"%(srcDir)
        d400 = "%s/3/400"%(srcDir)
        dsim = "%s/5/600"%(srcDir)
        
        data005, tnum005 = getAllData(d005,25, 70)
        data025, tnum025 = getAllData(d025, 3, 14)
        data125, tnum125 = getAllData(d125, 0, 14)
        data200, tnum200 = getAllData(d200, 0, 14)
        data400, tnum400 = getAllData(d400, 0, 14)
        datasim, tnumsim = getAllData(dsim,0, 14)
        
        bin005 = binCount(data005)/tnum005
        bin025 = binCount(data025)/tnum025
        bin125 = binCount(data125)/tnum125
        bin200 = binCount(data200)/tnum200
        bin400 = binCount(data400)/tnum400
        binsim = binCount(datasim)
                
        bin005 = bin005/binsim
        bin025 = bin025/binsim
        bin125 = bin125/binsim
        bin200 = bin200/binsim
        bin400 = bin400/binsim
        
        axs[0].plot(tbins, bin005, '+-', label='5 frame/combine')
        axs[0].plot(tbins, bin025, '.-', label='25 frame/combine')
        axs[0].plot(tbins, bin125, 'o-', label='125 frame/combine')
        axs[0].plot(tbins, bin200, '*-', label='200 frame/combine')
        axs[0].plot(tbins, bin400, '>-', label='400 frame/combine')
        axs[0].grid()
        axs[0].set_xticks(tbins)
        axs[0].legend(loc='upper right', framealpha=0.4)
        axs[0].set_title('%s sigma detect ratio from 2000 simulated stars'%(3))
        axs[0].set_ylabel('detection ratio')
        axs[0].set_xlabel('magnitude(R)')
        
        d005 = "%s/5/005"%(srcDir)
        d025 = "%s/5/025"%(srcDir)
        d125 = "%s/5/125"%(srcDir)
        d200 = "%s/5/200"%(srcDir)
        d400 = "%s/5/400"%(srcDir)
        
        data005, tnum005 = getAllData(d005,25, 70)
        data025, tnum025 = getAllData(d025, 3, 14)
        data125, tnum125 = getAllData(d125, 0, 14)
        data200, tnum200 = getAllData(d200, 0, 14)
        data400, tnum400 = getAllData(d400, 0, 14)
        
        bin005 = binCount(data005)/tnum005
        bin025 = binCount(data025)/tnum025
        bin125 = binCount(data125)/tnum125
        bin200 = binCount(data200)/tnum200
        bin400 = binCount(data400)/tnum400
                
        bin005 = bin005/binsim
        bin025 = bin025/binsim
        bin125 = bin125/binsim
        bin200 = bin200/binsim
        bin400 = bin400/binsim
        
        axs[1].plot(tbins, bin005, '+-', label='5 frame/combine')
        axs[1].plot(tbins, bin025, '.-', label='25 frame/combine')
        axs[1].plot(tbins, bin125, 'o-', label='125 frame/combine')
        axs[1].plot(tbins, bin200, '*-', label='200 frame/combine')
        axs[1].plot(tbins, bin400, '>-', label='400 frame/combine')
        axs[1].grid()
        axs[1].set_xticks(tbins)
        axs[1].legend(loc='upper right', framealpha=0.4)
        axs[1].set_title('%s sigma detect ratio from 2000 simulated stars'%(5))
        axs[1].set_ylabel('detection ratio')
        axs[1].set_xlabel('magnitude(R)')
        
        plt.savefig('%s/DetectRatio.png'%(destDir)) 
        
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        
def run1():
    
    srcPath = 'cmbDiffCat'
    destPath = "draw"
    
    if not os.path.exists(destPath):
        os.system("mkdir -p %s"%(destPath))            
    
    print("\n\n***************\nstatistic..\n")
    magStatistic1(srcPath, destPath)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()