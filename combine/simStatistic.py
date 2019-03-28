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
            os.system("mkdir -p %s"%(destFitDir))
            
        tfiles0 = os.listdir(srcFitDir)
        tfiles0.sort()
        
        tfiles = []
        for tfile in tfiles0:
            if len(tfile)==len('G031_mon_objt_190116T20334726_cmb005.cat'):
                tfiles.append(tfile)
        
        totalNum = len(tfiles)
        cmbNum = int(srcFitDir[-3:])
        sigma = int(srcFitDir[-5])

        if cmbNum>25:
            return
                
        sdatas = []
        starmchs = []
        galaxymchs = []
        for i in range(totalNum):
                        
            imgName = tfiles[i]
            
            imgpre= imgName.split(".")[0]
            tname0 = "%s/%s.cat"%(srcFitDir,imgpre)
            tname1 = "%s/%s_starmch.cat"%(srcFitDir,imgpre)
            tname3 = "%s/%s_galaxymch.cat"%(srcFitDir,imgpre)
            
            if os.path.exists(tname1) and os.path.exists(tname3):
            
                sdata = np.loadtxt(tname0)
                starmch = np.loadtxt(tname1)
                galaxymch = np.loadtxt(tname3)
                
                sdatas.append(sdata.shape[0])
                starmchs.append(starmch.shape[0])
                galaxymchs.append(galaxymch.shape[0])
            
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
        rightAxis0 = axes.twinx()
        pl1 = axes.plot(x, sdatas, 'r*-', label='star detected')
        axes.set_ylabel('length in a 10s exposure image(pixel)')
        #axes.set_xlabel('meteor height(km)')
        #plt.yticks( np.arange(4,53,4) )
        #axes.grid()
        #plt.xticks(np.arange(0, 24, 1.0))
        
        pl3 = rightAxis0.plot(x, starmchs, 'g>-',label='match sim star(2000)')
        pl4 = rightAxis0.plot(x, galaxymchs, 'b.-',label='match sim galaxy(1855)')
        rightAxis0.set_ylabel('plane height(km)')
        rightAxis0.grid()
        
        lns = pl1+pl3+pl4
        labs = [l.get_label() for l in lns]
        axes.legend(lns, labs, loc='upper right')
        #plt.show()
        plt.title('combine %d, %s sigma statistic'%(cmbNum, sigma))
        plt.savefig('%s/combine_%03d_sigma%s.png'%(destFitDir, cmbNum, sigma)) 
    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        
def simStatistic2(srcFitDir, destFitDir, start, end):
    
    try:
        if not os.path.exists(destFitDir):
            os.system("mkdir -p %s"%(destFitDir))
            
        cmbNum = int(srcFitDir[-3:])
        sigma = int(srcFitDir[-5])
        tfiles0 = os.listdir(srcFitDir)
        tfiles0.sort()
        
        tfiles = []
        for tfile in tfiles0:
            if len(tfile)==len('G031_mon_objt_190116T20334726_cmb005.cat'):
                tfiles.append(tfile)
        
        totalNum = len(tfiles)        
        starAll = np.array([])
        galaxyAll = np.array([])
        for i in range(totalNum):
            
            if i<start or i>end:
                continue
            
            imgName = tfiles[i]
            
            imgpre= imgName.split(".")[0]
            tname0 = "%s/%s.cat"%(srcFitDir,imgpre)
            tname1 = "%s/%s_starmch.cat"%(srcFitDir,imgpre)
            tname2 = "%s/%s_starnmh.cat"%(srcFitDir,imgpre)
            tname3 = "%s/%s_galaxymch.cat"%(srcFitDir,imgpre)
            tname4 = "%s/%s_galaxynmh.cat"%(srcFitDir,imgpre)
            
            starmch = np.loadtxt(tname1)
            galaxymch = np.loadtxt(tname3)
            
            starmchMag = starmch[:,2]
            galaxymchMag = galaxymch[:,2]
            
            if starAll.shape[0]==0:
                starAll = starmchMag
            else:
                starAll=np.concatenate((starAll, starmchMag), axis =0)
            if galaxyAll.shape[0]==0:
                galaxyAll = galaxymchMag
            else:
                galaxyAll=np.concatenate((galaxyAll, galaxymchMag), axis =0)
                
        print(starAll.shape)
        print(galaxyAll.shape)
        
        magCount1 = []
        for i in range(10):
            magCount1.append(0)
        
        for tmag in starAll:
            tIdx = int((tmag - 16)*10/2)
            if tIdx>9:
                tIdx=9
            if tIdx<0:
                tIdx=0
            magCount1[tIdx] = magCount1[tIdx] +1
            
        magCount2 = []
        for i in range(10):
            magCount2.append(0)
        
        for tmag in galaxyAll:
            tIdx = int((tmag - 16)*10/2)
            if tIdx>9:
                tIdx=9
            if tIdx<0:
                tIdx=0
            magCount2[tIdx] = magCount2[tIdx] +1
            
        tbins = np.linspace(16.1, 17.9, 10)
        magCount1 = np.array(magCount1)/starAll.shape[0]
        magCount2 = np.array(magCount2)/galaxyAll.shape[0]
        plt.figure(figsize=(8,4))
        plt.plot(tbins, magCount1, 'r*-', label='star %d(2000)'%(starAll.shape[0]/totalNum))
        plt.plot(tbins, magCount2, 'g.-', label='galaxy %d(1855)'%(galaxyAll.shape[0]/totalNum))
        plt.grid()
        plt.xticks(tbins)
        plt.legend(loc='upper right')
        plt.title('combine %d, %s sigma histogram'%(cmbNum, sigma))
        plt.savefig('%s/combine_%03d_sigma%s_hisGalaxy.png'%(destFitDir, cmbNum, sigma)) 
    
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        
def batchSimStatistic(srcDir, destDir):
    
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
                simStatistic1(sDirs, destDir)
                #break
            #break
        
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)
        
def batchSimStatistic2(srcDir, destDir):
    
    try:
        sDirs1 = "%s/3/005"%(srcDir)
        sDirs2 = "%s/3/025"%(srcDir)
        sDirs3 = "%s/3/125"%(srcDir)
        sDirs4 = "%s/3/200"%(srcDir)
        sDirs5 = "%s/3/400"%(srcDir)
        simStatistic2(sDirs1, destDir, 25, 70)
        simStatistic2(sDirs2, destDir, 0, 14)
        simStatistic2(sDirs3, destDir, 0, 14)
        simStatistic2(sDirs4, destDir, 0, 14)
        simStatistic2(sDirs5, destDir, 0, 14)
        
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
    batchSimStatistic2(srcPath, destPath)
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()