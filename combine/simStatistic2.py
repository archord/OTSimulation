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

def simStatistic1(srcFitDir, destFitDir):
    
    try:
        if not os.path.exists(destFitDir):
            os.system("mkdir %s"%(destFitDir))
            
        tfiles0 = os.listdir(srcFitDir)
        tfiles0.sort()
        
        tfiles = []
        for tfile in tfiles0:
            if len(tfile)==len('G031_mon_objt_190116T20323226_cmb400_starmch.cat') and tfile[-11:]=='starmch.cat':
                tfiles.append(tfile)
        
        totalNum = len(tfiles)
        print(totalNum)
        cmbNum = int(srcFitDir[-3:])
        sigma = int(srcFitDir[-5])

        if cmbNum>25:
            return
                
        sdatas = []
        for i in range(totalNum):
                        
            imgName = tfiles[i]
            tname0 = "%s/%s"%(srcFitDir,imgName)
            sdata = np.loadtxt(tname0)
            sdatas.append(sdata.shape[0])
            
            #break
        '''
        plt.figure(figsize=(12,6))
        plt.plot(sdatas,label='star detected')
        plt.plot(starmchs,label='match 2000 star simulation')
        plt.plot(galaxymchs,label='match 1855 galaxy simulation')
        
        plt.grid()
        plt.title('combine %d, %s sigma statistic'%(cmbNum, sigma))
        #plt.xticks(np.arange(0, 24, 1.0))
        #plt.xlim(0,24)
        plt.legend()
        plt.savefig('%s/combine_%03d_sigma%s.png'%(destFitDir, cmbNum, sigma)) 
        #plt.show()
        '''
        
        x = np.arange(1,len(sdatas)+1)
        fig, axes = plt.subplots(figsize=(12,6))
        axes.plot(x, sdatas, 'r*-', label='star recognized')
        axes.set_ylabel('number of stars')
        plt.grid()
        
        axes.legend(loc='upper right')
        plt.title('combine %d, %s sigma statistic'%(cmbNum, sigma))
        plt.savefig('%s/combine_recog_%03d_sigma%s.png'%(destFitDir, cmbNum, sigma)) 
    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        
        
def batchSimStatistic1(srcDir, destDir):
    
    try:
        
        tfiles0 = os.listdir(srcDir)
        
        for tfile in tfiles0:
            tpath1 = "%s/%s"%(srcDir, tfile)
            tfiles1 = os.listdir(tpath1)
            tfiles1.sort()
            tpaths = []
            for tfile2 in tfiles1:
                if len(tfile2)==3:
                    tpaths.append(tfile2)
            for tpath in tpaths:
                sDirs = "%s/%s"%(tpath1, tpath)
                print(sDirs)
                simStatistic1(sDirs, destDir)
                #break
            #break
        
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
    batchSimStatistic1(srcPath, destPath)
    
if __name__ == "__main__":
    
    run1()