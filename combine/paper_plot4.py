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
            if len(tfile)==len('G031_mon_objt_190116T20323226_cmb400_starmch.cat') and tfile[-11:]=='starmch.cat':
                tfiles.append(tfile)
        
        totalNum = len(tfiles)
        
        fileNum = 0
        allNum = 0
        mchNum = 0
        totNum = 0
        for i in range(totalNum):
            
            if i<start or i>end:
                continue
            
            imgName = tfiles[i]
            imgpre= imgName[:36]
            totName = "%s/%s_tot.cat"%(srcFitDir,imgpre)
            fotName = "%s/%s_fot.cat"%(srcFitDir,imgpre)
            mchName = "%s/%s_starmch.cat"%(srcFitDir,imgpre)
            
            if os.path.exists(totName) and os.path.exists(totName) and os.path.exists(totName):
                totData = np.loadtxt(totName)
                fotData = np.loadtxt(fotName)
                mchData = np.loadtxt(mchName)
                
                if mchData.shape[0]>0:
                    allNum += totData.shape[0]+fotData.shape[0]
                    mchNum += mchData.shape[0]
                    totNum += totData.shape[0]
                    fileNum += 1
                
        return allNum, totNum, mchNum, fileNum
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        return np.array([]), 0


def magStatistic1(srcDir, destDir):
    
    try:
    
        binNum = 10
        yticks = np.linspace(0, 1.0, 11)
        
        fig, axes = plt.subplots(1,2,figsize=(16,6))
        axs= axes.ravel()
        
        d005 = "%s/3/005"%(srcDir)
        d025 = "%s/3/025"%(srcDir)
        d125 = "%s/3/125"%(srcDir)
        d200 = "%s/3/200"%(srcDir)
        d400 = "%s/3/400"%(srcDir)
        dsim = "%s/5/600"%(srcDir)
        
        allNum005, totNum005, mchNum005, fileNum005 = getAllData(d005,5, 50)
        allNum025, totNum025, mchNum025, fileNum025 = getAllData(d025, 2, 8)
        allNum125, totNum125, mchNum125, fileNum125 = getAllData(d125, 0, 14)
        allNum200, totNum200, mchNum200, fileNum200 = getAllData(d200, 0, 14)
        allNum400, totNum400, mchNum400, fileNum400 = getAllData(d400, 0, 14)
        allNumSim, totNumSim, mchNumSim, fileNumSim = getAllData(dsim,0, 14)
        
        if allNum005==0:
            bin005 = 0
        else:
            bin005 = mchNum005*1.0/allNum005
        if allNum025==0:
            bin025 = 0
        else:
            bin025 = mchNum025*1.0/allNum025
        if allNum125==0:
            bin125 = 0
        else:
            bin125 = mchNum125*1.0/allNum125
        if allNum200==0:
            bin200 = 0
        else:
            bin200 = mchNum200*1.0/allNum200
        if allNum400==0:
            bin400 = 0
        else:
            bin400 = mchNum400*1.0/allNum400
        
        #y11 = [bin005, bin025, bin125,bin200, bin400]
        y11 = [bin005, bin025, bin125, bin400]
        print(y11)
        
        if allNum005==0:
            bin005 = 0
        else:
            bin005 = mchNum005*1.0/fileNum005/allNumSim
        if allNum025==0:
            bin025 = 0
        else:
            bin025 = mchNum025*1.0/fileNum025/allNumSim
        if allNum125==0:
            bin125 = 0
        else:
            bin125 = mchNum125*1.0/fileNum125/allNumSim
        if allNum200==0:
            bin200 = 0
        else:
            bin200 = mchNum200*1.0/fileNum200/allNumSim
        if allNum400==0:
            bin400 = 0
        else:
            bin400 = mchNum400*1.0/fileNum400/allNumSim
        
        #y12 = [bin005, bin025, bin125,bin200, bin400]
        y12 = [bin005, bin025, bin125, bin400]
        print(y12)
        
        d005 = "%s/5/005"%(srcDir)
        d025 = "%s/5/025"%(srcDir)
        d125 = "%s/5/125"%(srcDir)
        d200 = "%s/5/200"%(srcDir)
        d400 = "%s/5/400"%(srcDir)
        
        allNum005, totNum005, mchNum005, fileNum005 = getAllData(d005,5, 50)
        allNum025, totNum025, mchNum025, fileNum025 = getAllData(d025, 2, 8)
        allNum125, totNum125, mchNum125, fileNum125 = getAllData(d125, 0, 14)
        allNum200, totNum200, mchNum200, fileNum200 = getAllData(d200, 0, 14)
        allNum400, totNum400, mchNum400, fileNum400 = getAllData(d400, 0, 14)
        
        if allNum005==0:
            bin005 = 0
        else:
            bin005 = mchNum005*1.0/allNum005
        if allNum025==0:
            bin025 = 0
        else:
            bin025 = mchNum025*1.0/allNum025
        if allNum125==0:
            bin125 = 0
        else:
            bin125 = mchNum125*1.0/allNum125
        if allNum200==0:
            bin200 = 0
        else:
            bin200 = mchNum200*1.0/allNum200
        if allNum400==0:
            bin400 = 0
        else:
            bin400 = mchNum400*1.0/allNum400
        
        #y21 = [bin005, bin025, bin125,bin200, bin400]
        y21 = [bin005, bin025, bin125, bin400]
        print(y21)
        
        if allNum005==0:
            bin005 = 0
        else:
            bin005 = mchNum005*1.0/fileNum005/allNumSim
        if allNum025==0:
            bin025 = 0
        else:
            bin025 = mchNum025*1.0/fileNum025/allNumSim
        if allNum125==0:
            bin125 = 0
        else:
            bin125 = mchNum125*1.0/fileNum125/allNumSim
        if allNum200==0:
            bin200 = 0
        else:
            bin200 = mchNum200*1.0/fileNum200/allNumSim
        if allNum400==0:
            bin400 = 0
        else:
            bin400 = mchNum400*1.0/fileNum400/allNumSim
        
        #y22 = [bin005, bin025, bin125,bin200, bin400]
        y22 = [bin005, bin025, bin125, bin400]
        print(y22)
        
        #x = [1,2,3,4,5]
        #xlabel = [5,25,125,200,400]
        x = [1,2,3,4]
        xlabel = [5,25,125,400]
        
        axs[0].plot(x, y11, '*-', label='3 sigma')
        axs[0].plot(x, y12, '>-', label='5 sigma')
        axs[0].grid()
        axs[0].set_xticks(x)
        #axs[0].set_yticks(yticks)
        #axs[0].set_ylim((0, 1))
        axs[0].set_xticklabels(xlabel)
        axs[0].legend(loc='upper right', framealpha=0.4)
        axs[0].set_title('success ratio of residual image with 2000 simulated stars')
        axs[0].set_ylabel('ratio')
        axs[0].set_xlabel('image combine number')
        
        axs[1].plot(x, y21, '*-', label='3 sigma')
        axs[1].plot(x, y22, '>-', label='5 sigma')
        axs[1].grid()
        axs[1].set_xticks(x)
        #axs[1].set_yticks(yticks)
        #axs[0].set_ylim((0, 1))
        axs[1].set_xticklabels(xlabel)
        axs[1].legend(loc='upper right', framealpha=0.4)
        axs[1].set_title('detect ratio of 2000')
        axs[1].set_ylabel('ratio')
        axs[1].set_xlabel('image combine number')
        
        plt.savefig('%s/RealDetectRatio.png'%(destDir)) 
        
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        
def run1():
    
    srcPath = 'otrcg'
    destPath = "draw"
    
    if not os.path.exists(destPath):
        os.system("mkdir -p %s"%(destPath))            
    
    print("\n\n***************\nstatistic..\n")
    magStatistic1(srcPath, destPath)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()