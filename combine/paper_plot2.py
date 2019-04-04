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
        
        fileNum = 0
        allNum = 0
        mchNum = 0
        for i in range(totalNum):
            
            if i<start or i>end:
                continue
            
            imgName = tfiles[i]
            imgpre= imgName.split(".")[0]
            tname0 = "%s/%s.cat"%(srcFitDir,imgpre)
            tname1 = "%s/%s_starmch.cat"%(srcFitDir,imgpre)
            
            starall = np.loadtxt(tname0)
            starmch = np.loadtxt(tname1)
            
            allNum += starall.shape[0]
            mchNum += starmch.shape[0]
            fileNum += 1
                
        return allNum, mchNum, fileNum
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        return np.array([]), 0


def magStatistic1(srcDir, destDir):
    
    try:
    
        binNum = 10
        yticks = np.linspace(0, 1.0, 11)
        
        fig, axes = plt.subplots(1,2,figsize=(20,8))
        axs= axes.ravel()
        
        d005 = "%s/3/005"%(srcDir)
        d025 = "%s/3/025"%(srcDir)
        d125 = "%s/3/125"%(srcDir)
        d200 = "%s/3/200"%(srcDir)
        d400 = "%s/3/400"%(srcDir)
        dsim = "%s/5/600"%(srcDir)
        
        allNum005, mchNum005, fileNum005 = getAllData(d005,25, 70)
        allNum025, mchNum025, fileNum025 = getAllData(d025, 3, 14)
        allNum125, mchNum125, fileNum125 = getAllData(d125, 0, 14)
        allNum200, mchNum200, fileNum200 = getAllData(d200, 0, 14)
        allNum400, mchNum400, fileNum400 = getAllData(d400, 0, 14)
        allNumSim, mchNumSim, fileNumSim = getAllData(dsim,0, 14)
                        
        bin005 = mchNum005*1.0/allNum005
        bin025 = mchNum025*1.0/allNum025
        bin125 = mchNum125*1.0/allNum125
        bin200 = mchNum200*1.0/allNum200
        bin400 = mchNum400*1.0/allNum400
        
        y11 = [bin005, bin025, bin125,bin200, bin400]
        bin005 = mchNum005*1.0/fileNum005/allNumSim
        bin025 = mchNum025*1.0/fileNum025/allNumSim
        bin125 = mchNum125*1.0/fileNum125/allNumSim
        bin200 = mchNum200*1.0/fileNum200/allNumSim
        bin400 = mchNum400*1.0/fileNum400/allNumSim
        
        y12 = [bin005, bin025, bin125,bin200, bin400]
        
        d005 = "%s/5/005"%(srcDir)
        d025 = "%s/5/025"%(srcDir)
        d125 = "%s/5/125"%(srcDir)
        d200 = "%s/5/200"%(srcDir)
        d400 = "%s/5/400"%(srcDir)
        
        allNum005, mchNum005, fileNum005 = getAllData(d005,25, 70)
        allNum025, mchNum025, fileNum025 = getAllData(d025, 3, 14)
        allNum125, mchNum125, fileNum125 = getAllData(d125, 0, 14)
        allNum200, mchNum200, fileNum200 = getAllData(d200, 0, 14)
        allNum400, mchNum400, fileNum400 = getAllData(d400, 0, 14)
                        
        bin005 = mchNum005*1.0/allNum005
        bin025 = mchNum025*1.0/allNum025
        bin125 = mchNum125*1.0/allNum125
        bin200 = mchNum200*1.0/allNum200
        bin400 = mchNum400*1.0/allNum400
        
        y21 = [bin005, bin025, bin125,bin200, bin400]
        bin005 = mchNum005*1.0/fileNum005/allNumSim
        bin025 = mchNum025*1.0/fileNum025/allNumSim
        bin125 = mchNum125*1.0/fileNum125/allNumSim
        bin200 = mchNum200*1.0/fileNum200/allNumSim
        bin400 = mchNum400*1.0/fileNum400/allNumSim
        
        
        y22 = [bin005, bin025, bin125,bin200, bin400]
        x = [1,2,3,4,5]
        xlabel = [5,25,125,200,400]
        
        axs[0].plot(x, y11, '*-', label='3 sigma')
        axs[0].plot(x, y21, '>-', label='5 sigma')
        axs[0].grid()
        axs[0].set_xticks(x)
        #axs[0].set_yticks(yticks)
        #axs[0].set_ylim((0, 1))
        axs[0].set_xticklabels(xlabel)
        axs[0].legend(loc='upper right', framealpha=0.4)
        axs[0].set_title('success ratio of residual image with 2000 simulated stars')
        axs[0].set_ylabel('ratio')
        axs[0].set_xlabel('image combine number')
        
        axs[1].plot(x, y12, '*-', label='3 sigma')
        axs[1].plot(x, y22, '>-', label='5 sigma')
        axs[1].grid()
        axs[1].set_xticks(x)
        #axs[1].set_yticks(yticks)
        #axs[0].set_ylim((0, 1))
        axs[1].set_xticklabels(xlabel)
        axs[1].legend(loc='upper left', framealpha=0.9)
        #axs[1].set_title('detect ratio of 2000')
        axs[1].set_ylabel('Detection Percentage (R<18mag)')
        axs[1].set_xlabel('Frame of Images to be Stacked')
        
        plt.savefig('%s/RealDetectRatio.png'%(destDir)) 
        
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