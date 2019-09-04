# -*- coding: utf-8 -*-
import numpy as np
import os
from datetime import datetime
import traceback
import psycopg2
import cv2
import matplotlib.pyplot as plt
from astropy.wcs import WCS
#from astrotools import AstroTools
from astropy.io import fits
import math
from scipy.spatial import KDTree
from match1 import StarMatch


#   1 X_IMAGE                Object position along x                                    [pixel]
#   2 Y_IMAGE                Object position along y                                    [pixel]
#   9 BACKGROUND             Background at centroid position                            [count]
#  10 FWHM_IMAGE             FWHM assuming a gaussian core                              [pixel]
#  12 MAG_APER               Fixed aperture magnitude vector                            [mag]
#  13 MAGERR_APER            RMS error vector for fixed aperture mag.                   [mag]
def getSubCat():
    
    srcDir = "/data/gwac_diff_xy/matchTest/cat"
    dstDir = "/data/gwac_diff_xy/matchTest/tmp"
    dataNPZ = '%s/catDiff.npz'%(dstDir)
    
    cats = os.listdir(srcDir)
    
    tIdx = np.array([0,1,8,9,11,12])
    fnames = []
    datas = []
    for tcat in cats:
        spath1 = "%s/%s"%(srcDir,tcat)
        tdata = np.loadtxt(spath1, dtype=np.float32)
        tdata = tdata[:,tIdx]
        fnames.append(tcat)
        datas.append(tdata)
    
    np.savez_compressed(dataNPZ,fns=fnames, ds=datas)


def imgStatistic(size=2000):
    
    dstDir = "/data/gwac_diff_xy/matchTest/tmp"
    dataNPZ = '%s/catDiff.npz'%(dstDir)
    
    allDatas = np.load(dataNPZ)
    fnames = allDatas['fns']
    datas = allDatas['ds']
    
    imgSize = (4136, 4196)
    #imgSize = (4136, 4096)
    imgW = imgSize[1]
    imgH = imgSize[0]
    
    halfSize = size/2
    xStart = int(imgW/2 - halfSize)
    xEnd = int(imgW/2 + halfSize)
    yStart = int(imgH/2 - halfSize)
    yEnd = int(imgH/2 + halfSize)
    
    evaDatas = []
    for i, catData in enumerate(datas):
        totalStarNum = len(catData)
        fname = fnames[i] #G023_mon_objt_190302T11402824.cat
        dateStr = fname[14:27] #190302T114028
        camName = fname[2:4] #23
        fwhms = []
        bkgs = []
        for row in catData:
            tx = row[0]
            ty = row[1]
            fwhm = row[3]
            bkg = row[2]
            if tx>=xStart and tx<xEnd and ty>=yStart and ty<yEnd:
                fwhms.append(fwhm)
                bkgs.append(bkg)
        
        fwhms = np.array(fwhms)
        bkgs = np.array(bkgs)
        
        times = 2
        for i in range(1):
            tmean = np.mean(fwhms)
            trms = np.std(fwhms)
            tIdx = fwhms<(tmean+times*trms)
            fwhms = fwhms[tIdx]
            
            tmean = np.mean(bkgs)
            trms = np.std(bkgs)
            tIdx = bkgs<(tmean+times*trms)
            bkgs = bkgs[tIdx]
            
        fwhmMean = np.mean(fwhms)
        fwhmRms = np.std(fwhms)
        bkgMean = np.mean(bkgs)
        bkgRms = np.std(bkgs)
        evaDatas.append([dateStr, camName, totalStarNum, fwhmMean, fwhmRms, bkgMean, bkgRms])
    
    evaDatas = np.array(evaDatas)
    dstDir = "/data/gwac_diff_xy/matchTest/tmp"
    dataNPZ = '%s/statisticData.npz'%(dstDir)
    np.savez_compressed(dataNPZ,ed=evaDatas)

def fwhmBkgStatistic():
    
    dstDir = "/data/gwac_diff_xy/matchTest/tmp"
    #dstDir = "data"
    catNPZ = '%s/catDiff.npz'%(dstDir)
    sttNPZ = '%s/statisticData.npz'%(dstDir)
    
    tdata2 = np.load(sttNPZ)
    evaDatas = tdata2['ed']
    print(evaDatas.shape)
    print(evaDatas[:3])
    
    fwhm = evaDatas[:,3].astype(np.float)
    starNum = evaDatas[:,2].astype(np.int)
    print(np.max(fwhm))
    print(np.min(fwhm))
    fwhm2 = fwhm[fwhm<3]
    starNum2 = starNum[fwhm<3]
    '''
    plt.hist(fwhm2,bins=20, )
    plt.show()
    plt.hist(starNum2,bins=20, )
    plt.show()
    '''
    print(starNum2[fwhm2<1.65])
    
    
    tdata1 = np.load(catNPZ)
    fnames = tdata1['fns']
    fnames = np.array(fnames)
    fnames2 = fnames[(np.abs(fwhm-1.9)<0.01) & (np.abs(starNum-10000)<2000)]
    print(fnames2)
    '''
    ['G024_mon_objt_181018T18570151.cat' 'G024_mon_objt_181018T19031651.cat'
     'G021_mon_objt_181101T17255569.cat' 'G023_mon_objt_181118T14200302.cat'
     'G034_mon_objt_181209T16395419.cat' 'G034_mon_objt_181209T17172419.cat'
     'G033_mon_objt_181217T14013054.cat' 'G021_mon_objt_181225T15082136.cat'
     'G034_mon_objt_181226T12593001.cat' 'G021_mon_objt_181227T15085136.cat'
     'G024_mon_objt_181229T14215937.cat' 'G031_mon_objt_190110T15230409.cat'
     'G043_mon_objt_190126T10594812.cat' 'G031_mon_objt_190204T12403703.cat']
    '''
    return fnames2
    
def imgMatch():
    
    srcDir = "/data/gwac_diff_xy/matchTest/cat"
    dstDir = "/data/gwac_diff_xy/matchTest/tmp"
    
    tmplCat0 = ['G021_mon_objt_181101T17255569.cat',
                'G032_mon_objt_190110T14080401.cat',
                'G043_mon_objt_190126T10594812.cat',
                'G024_mon_objt_181018T18570151.cat']
    
    objCats = os.listdir(srcDir)
    
    starMatch = StarMatch()
    
    for tmplCat in tmplCat0:
        print("\n*****************************\n")
        print("temp %s match..."%(tmplCat))
        tmplCatPath = '%s/%s'%(srcDir, tmplCat)
        tmplCCDNum = tmplCat[3]
        
        savePath = "%s/%s_mch1.cat"%(dstDir,tmplCat.split('.')[0])
        tf = open(savePath, 'w')
        tf.write("#fname, starNum, featureNum, matchNum, micro seconds\n")
        
        tiData = np.loadtxt(tmplCatPath)
        print("orign")
        print(tiData.shape)
        tiData = starMatch.filterStar(tiData, xIdx=0, yIdx=1)
        print("filter")
        print(tiData.shape)
        
        brightStarTi, darkStarTi = starMatch.getBright(tiData,100, 11)
        print("bright")
        print(brightStarTi.shape)
        print("dark")
        print(darkStarTi.shape)
        
        regionPosTi, regionStarNumTi, regNumTi, regSizeTi, regWTi, regHTi = starMatch.createRegionIdx(darkStarTi)
        starMatch.statisticRegions(regionPosTi, regionStarNumTi)
        tiXY, mchIdxsTi = starMatch.createMatchIdx(brightStarTi, regionPosTi, regNumTi, regSizeTi, regWTi, regHTi)
        
        tarray = np.array(mchIdxsTi)
        print(tarray.shape)
        tDist = tarray[:,:,2]
        print(tDist.shape)
        tree = KDTree(tDist)
        
        #G021_mon_objt_181101T17255569.cat
        for objCat in objCats:
            ccdNum = objCat[3]
            if ccdNum == tmplCCDNum and tmplCat!=objCat:
                spath1 = "%s/%s"%(srcDir,objCat)
                
                starttime = datetime.now()
                oiData = np.loadtxt(spath1, dtype=np.float32)
                starNum = oiData.shape[0]
                
                oiData = starMatch.filterStar(oiData, xIdx=0, yIdx=1)
                brightStarOi, darkStarOi = starMatch.getBright(oiData, 100, 11)
                regionPosOi, regionStarNumOi, regNumOi, regSizeOi, regWOi, regHOi = starMatch.createRegionIdx(darkStarOi)
                
                oiXY, mchIdxsOi = starMatch.createMatchIdx(brightStarOi, regionPosOi, regNumOi, regSizeOi, regWOi, regHOi)
                if len(mchIdxsOi)==0:
                    print("%s searchR %d create feature failure, reuse %d"%(objCat, regSizeOi, regSizeOi*2))
                    oiXY, mchIdxsOi = starMatch.createMatchIdx(brightStarOi, regionPosOi, regNumOi, regSizeOi, regWOi, regHOi, 10, 4)
    
                totalMatchNum = 0
                mchList = []
                mchRadius = [20,40,100]
                for tr in mchRadius:
                    for i, oIdx in enumerate(mchIdxsOi):
                        td = oIdx[:,2]
                        mchIdx = tree.query_ball_point(td, tr)
                        
                        if len(mchIdx)>0:
                            for tidx0 in mchIdx:
                                tdata00 = tarray[tidx0]
                                dm, isMchOk = starMatch.distMatch(oIdx, tdata00)
                                if len(dm)>2 and isMchOk:
                                    omIdx = dm[:,0]
                                    tmIdx = dm[:,1]
                                    oxy01 = oiXY[i]
                                    txy02 = tiXY[tidx0]
                                    opos = omIdx[:,0:2]
                                    tpos = tmIdx[:,0:2]
                                    oxy1 = np.concatenate([opos,[oxy01]])
                                    txy1 = np.concatenate([tpos,[txy02]])
                                    mchList.append((oxy1,txy1))
                                    totalMatchNum += 1
                                    break
                    if len(mchList)>1:
                        break
                    else:
                        mchList = []
                        print("%s radius %d matchNum %d"%(objCat, tr, len(mchList)))

                endtime = datetime.now()
                runTime = (endtime - starttime).total_seconds()*1000
                print("%s, starNum=%d, featureNum=%d, matchNum=%d, blind match use %d micro seconds"\
                      %(objCat, starNum, len(mchIdxsOi),  totalMatchNum, runTime))
                tf.write("%s, %d, %d, %d, %d\n"\
                      %(objCat, starNum, len(mchIdxsOi),  totalMatchNum, runTime))
                tf.flush()
                
                if len(mchList)>0:
                    '''
                    starttime = datetime.now()
                    darkStarOiTi = starMatch.posTrans(mchList, darkStarOi)
                    endtime = datetime.now()
                    runTime = (endtime - starttime).total_seconds()*1000
                    print("********** trans %s use %d micro seconds"%(objCat, runTime))
                    
                    starttime = datetime.now()
                    origXY, mchXY = starMatch.match(darkStarOiTi, regionPosTi, regNumTi, regSizeTi, regWTi, regHTi,1)
                    endtime = datetime.now()
                    runTime = (endtime - starttime).seconds
                    print("********** rematch %s use %d seconds"%(objCat, runTime))
                    
                    mchXY = np.array(mchXY)
                    tdist = mchXY[:,2]
                    minD = np.min(tdist)
                    maxD = np.max(tdist)
                    avgD = np.mean(tdist)
                    print("minD=%f,maxD=%f,avgD=%f"%(minD, maxD, avgD))
                    print("origNum:%d, after:%d"%(darkStarOiTi.shape[0],mchXY.shape[0]))
                    '''
        tf.close()
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
    
    #getSubCat()
    #imgStatistic()
    #fwhmBkgStatistic()
    imgMatch()