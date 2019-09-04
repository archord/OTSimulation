# -*- coding: utf-8 -*-
import numpy as np
import math
from astropy.io import fits
import os
import traceback
from datetime import datetime
from blindmatch import removeHeaderAndOverScan2, doAll

def doAlign(cats, dateDir, saveDir):
    
    catPath = '/home/xy/work/imgDiffTest2/cat/%s'%(dateDir)
    fitPath = '/home/xy/work/imgDiffTest2/fits/%s'%(dateDir)

    tiCat = cats[0].decode("utf-8") 
    print("template %s"%(tiCat))
    
    theader, imgData = removeHeaderAndOverScan2(fitPath, "%s.fit.fz"%(tiCat.split('.')[0]))
    savePath = "%s/%s.fit"%(saveDir, tiCat.split('.')[0])
    fits.writeto(savePath, imgData, header=theader, overwrite=True)
        
    for i in range(len(cats)):
        if i>0:
            oiCat = cats[i].decode("utf-8") 
            print("observate %s"%(oiCat))
            tpre = oiCat.split('.')[0]
            oiFit = "%s.fit.fz"%(tpre)
    
            try:
                doAll(catPath, tiCat, catPath, oiCat, fitPath, oiFit, saveDir)
                
            except Exception as e:
                print(e)
                tstr = traceback.format_exc()
                print(tstr)
                
def align(cmbNum):
    
    tpath1 = '/home/xy/work/imgDiffTest2/cat'
    tpath2 = '/home/xy/work/imgDiffTest2/align/%03d'%(cmbNum)
    if not os.path.exists(tpath2):
        os.mkdir(tpath2)
    
    dateDirs = os.listdir(tpath1)
    for tdate in dateDirs:
        print("process %s"%(tdate))
        tpath3 = "%s/%s"%(tpath1, tdate)
        destPath = "%s/%s"%(tpath2, tdate)
        if not os.path.exists(destPath):
            os.mkdir(destPath)
        
        cats = os.listdir(tpath3)
        tparms = []
        for i, tcat in enumerate(cats):
            catPath = "%s/%s"%(tpath3, tcat)
            tdata =  np.loadtxt(catPath)
            starNum = tdata.shape[0]
            fwhmMedian = np.median(tdata[:,9])
            tparms.append((tcat,starNum, fwhmMedian))
            #if i>50:
            #    break
        
        dtype = [('cat_name', 'S40'), ('starNum', int), ('fwhm', float)]
        tparms=np.array(tparms, dtype=dtype)
        print("total read %d catFiles"%(tparms.shape[0]))
        #tparms = np.sort(tparms,order=['fwhm', 'starNum'])
        #minfwhm = tparms[tparms['fwhm']==tparms[0][2]]
        tparms = np.sort(tparms,order=['starNum'])
        maxStarNum = tparms[-cmbNum:]
        #print(maxStarNum)
        doAlign(maxStarNum['cat_name'], tdate, destPath)
        #break
        
def combineAlign():
    
    catDir = '/home/xy/work/imgDiffTest2/combineCat'
    tpath1 = '/home/xy/work/imgDiffTest2/combine2'
    tpath2 = '/home/xy/work/imgDiffTest2/combineAlign'
    if not os.path.exists(tpath2):
        os.mkdir(tpath2)
    
    dateDirs = os.listdir(tpath1)
    for tdate in dateDirs:
        print("\n\n*****process %s"%(tdate))
        tpath3 = "%s/%s"%(tpath1, tdate)
        destPath = "%s/%s"%(tpath2, tdate)
        if not os.path.exists(destPath):
            os.mkdir(destPath)
        
        cats = os.listdir(tpath3)
        cats.sort()
        
        tcat = cats[0]
        print("select %s as template"%(tcat))
        camName = tcat[:4]
        dateStr = tcat[14:20]
        tdir = "%s_G0%s_%s"%(dateStr,camName[1:3], camName[1:])
        catPath1 = "%s/%s"%(catDir,tdate)
        tiCat = "%s.cat"%(tcat.split('.')[0])
        os.system("cp %s/%s %s/%s"%(tpath3, tcat, destPath, tcat))
        
        for i, cat in enumerate(cats):
            if i>0:
                tcat = cats[i]
                oiFit = tcat
                camName = tcat[:4]
                dateStr = tcat[14:20]
                tdir = "%s_G0%s_%s"%(dateStr,camName[1:3], camName[1:])
                print(tdir)
                catPath2 = "%s/%s"%(catDir,tdate)
                oiCat = "%s.cat"%(tcat.split('.')[0])
                doAll(catPath1, tiCat, catPath2, oiCat, tpath3, oiFit, destPath)
                
            #if i>2:
            #    break
        #break
        
def superCombine(srcFitDir, destFitDir, regions=[2,2]):

    try:
        tfiles0 = os.listdir(srcFitDir)
        tfiles0.sort()
        print("total combine %d images"%(len(tfiles0)))
        starttime = datetime.now()
        
        tCmbImg = np.array([])
        regWid = 0
        regHei = 0
        for ty in range(regions[0]):
            for tx in range(regions[1]):
                imgs = []
                for j in range(len(tfiles0)):
                    tname = tfiles0[j]
                    tdata1 = fits.getdata("%s/%s"%(srcFitDir, tname),ext=0) #first image is template
                    if tCmbImg.shape[0]==0:
                        tCmbImg=tdata1.copy()
                        regWid = int(tCmbImg.shape[1]/2)
                        regHei = int(tCmbImg.shape[0]/2)
                    imgs.append(tdata1[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid].copy())
                    '''
                    with fits.open("%s/%s"%(srcFitDir, tname), mode='readonly', memmap=True, do_not_scale_image_data=True) as hdulist: #
                        tdata1 = hdulist[0].data
                        if tCmbImg.shape[0]==0:
                            tCmbImg=tdata1.copy()
                            print(tCmbImg.shape)
                            print(type(tCmbImg[0][0]))
                            regWid = int(tCmbImg.shape[1]/2)
                            regHei = int(tCmbImg.shape[0]/2)
                        imgs.append(tdata1[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid].copy())
                        del hdulist[0].data
                    '''
                imgArray = np.array(imgs)
                tCmbImg[ty*regHei:(ty+1)*regHei, tx*regWid:(tx+1)*regWid] = np.median(imgArray,axis=0)
        
        #tCmbImg = tCmbImg.astype(np.uint16)
        outImgName = "%s_cmb%03d"%(tfiles0[0].split('.')[0], len(tfiles0))
        fits.writeto("%s/%s.fit"%(destFitDir, outImgName), tCmbImg, overwrite=True)
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        print("combine use %d seconds"%(runTime))
        
    except Exception as e:
        print(str(e))
        tstr = traceback.format_exc()
        print(tstr)

def batchCombine():
    
    tpath1 = '/home/xy/work/imgDiffTest2/align'
    tpath2 = '/home/xy/work/imgDiffTest2/combine2'
    if not os.path.exists(tpath2):
        os.mkdir(tpath2)
    
    cmbDirs = os.listdir(tpath1)
    cmbDirs.sort()
    for cmb in cmbDirs:
        print("process combine %s"%(cmb))
        tpath4 = "%s/%s"%(tpath1, cmb)
        dateDirs = os.listdir(tpath4)
        for tdate in dateDirs:
            print("process %s"%(tdate))
            tpath3 = "%s/%s"%(tpath4, tdate)
            superCombine(tpath3, tpath2)
            #break
        #break
    
if __name__ == "__main__":
    '''
    align(5)
    align(25)
    align(125)
    '''
    #batchCombine()
    combineAlign()