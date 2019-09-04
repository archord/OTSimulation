# -*- coding: utf-8 -*-
import numpy as np
import math
import cv2
import os
import matplotlib.pyplot as plt
import warnings
import traceback
from astropy.modeling import models, fitting
from scipy.spatial import KDTree
from datetime import datetime
from crossmatch import CrossMatch
            
class BlindMatch(object):
    
    def __init__(self): 
        self.imgW = 4096
        self.imgH = 4136
        #regionBorder=[minX,maxX,minY,maxY]
        self.regionBorder=[100,4000,100,4000]
        #self.regionBorder=[0,4096,0,4136]
        
        self.regNum = 0
        self.regSize = 0
        self.regW = 0
        self.regH = 0
        self.magIdx = 11
        self.xIdx = 0
        self.yIdx = 1
             
    def getLineDistance(self, star1, star2):
        
        tx = star1[0] - star2[0]
        ty = star1[1] - star2[1]
        tdist = math.sqrt(tx*tx+ty*ty)
        return tdist
    
    def evaluatePos(self, pos1, pos2, isAbs=False):
        
        if isAbs:
            posDiff = np.fabs(pos1 - pos2)
        else:
            posDiff = pos1 - pos2
        tmean = np.mean(posDiff, axis=0)
        tmax = np.max(posDiff, axis=0)
        tmin = np.min(posDiff, axis=0)
        trms = np.std(posDiff, axis=0)
        xshift = tmean[0]
        yshift = tmean[1]
        xrms = trms[0]
        yrms = trms[1]
        
        return xshift,yshift, xrms, yrms
    
    def createBlindMatchFeatures(self, stars, featurePoint=160, featureNum=10, searchRTimes=2, partitionNum=4):
        
        oiMatch = CrossMatch()
        oiData = oiMatch.filterStar(stars)
        brightStarOi, darkStarOi = oiMatch.getBright(oiData, featurePoint)
        '''
        tpos = brightStarOi[:,0:2].copy()
        tpos[:,0] = tpos[:,0] + 20
        self.saveReg(tpos, "data/reg%d.reg"%(stars.shape[0]), radius=4, width=1, color='green')
        '''    
        oiMatch.createRegionIdx(darkStarOi, featureNum)
        #oiMatch.statisticRegions()
        
        searchRadius = oiMatch.regSize*searchRTimes
        
        tXY = []
        mchIdxs = []
        for i, ts in enumerate(brightStarOi):
            x = ts[0]
            y = ts[1]
            nN = oiMatch.getNearestN(x,y, searchRadius,featureNum)
            if len(nN)==featureNum:
                tXY.append((x,y))
                mchIdxs.append(nN)
        
        return tXY, mchIdxs
    
    def plotBlindMatch(self, x1, y1, xs1, ys1, x2, y2, xs2, ys2):
        
        fig, axes = plt.subplots(1,2,figsize=(8,3))
        axs= axes.ravel()
        
        for i,tx1 in enumerate(xs1):
            tx = xs1[i]
            ty = ys1[i]
            axs[0].plot((x1,tx),(y1,ty))
            
        for i,tx1 in enumerate(xs2):
            tx = xs2[i]
            ty = ys2[i]
            axs[1].plot((x2,tx),(y2,ty))
        axs[0].grid()
        axs[1].grid()
        plt.show()
                    
    '''
    两组排序的（数值由小到大）特征匹配，每次重新循环，找距离最近的，可能重复匹配
    '''
    def blindDistMatch(self, oiData, tiData, maxMchDist=1, minMchNum=3):
        
        oiDist = oiData[:,2]
        tiDist = tiData[:,2]

        mchPairs = []
        mchNum = 0
        distError = 0
        minDiff = maxMchDist
        minDiffIdx = -1
        for oi, oiD in enumerate(oiDist):
            for ti, tiD in enumerate(tiDist):
                tdiff = math.fabs(oiD-tiD)
                if tdiff<minDiff:
                    minDiff = tdiff
                    minDiffIdx = ti
            if minDiffIdx>-1:
                mchPairs.append((oiData[oi],tiData[minDiffIdx]))
                mchNum = mchNum +1
                distError += minDiff
                minDiff = maxMchDist
                minDiffIdx = -1
        
        meanError = 99
        if mchNum>0:
            meanError = distError/mchNum
            #print("mchNum=%d,meanError=%f"%(mchNum,meanError))
        
        isMchOk = True
        if mchNum>=minMchNum:
            for i, mp in enumerate(mchPairs):
                p1 = mchPairs[i]
                if i==mchNum-1:
                    p2 = mchPairs[0]
                else:
                    p2 = mchPairs[i+1]
                op1 = p1[0]
                tp1 = p1[1]
                op2 = p2[0]
                tp2 = p2[1]
                tdist1 = self.getLineDistance((op1[0],op1[1]),(op2[0],op2[1]))
                tdist2 = self.getLineDistance((tp1[0],tp1[1]),(tp2[0],tp2[1]))
                tdiff = np.fabs(tdist1-tdist2)
                if tdiff>maxMchDist:
                    isMchOk = False
                    break
        else:
            isMchOk = False
            
        return np.array(mchPairs), isMchOk
            
    def saveReg(self, pos, fname, radius=4, width=1, color='green'):
        
        with open(fname, 'w') as fp1:
            for tobj in pos:
               fp1.write("image;circle(%.2f,%.2f,%.2f) # color=%s width=%d font=\"times 10\"\n"%
               (tobj[0], tobj[1], radius, color, width))
        
    def posTransPerspective(self, posMchs, stars):
        
        for i, tm in enumerate(posMchs):
            if i==0:
                dataOi = posMchs[i][0]
                dataTi = posMchs[i][1]
            else:
                dataOi = np.concatenate([dataOi,posMchs[i][0]])
                dataTi = np.concatenate([dataTi,posMchs[i][1]])
        
        xshift,yshift, xrms, yrms = self.evaluatePos(dataOi, dataTi)
        print("%d blindMatch stars, before trans: \nxshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(dataOi.shape[0], xshift,yshift, xrms, yrms))
                
        h, tmask = cv2.findHomography(dataOi, dataTi, cv2.RANSAC, 0.1) #0, RANSAC , LMEDS
        
        dataTi2 = cv2.perspectiveTransform(np.array([dataOi]), h)
        dataTi2 = dataTi2[0]
        
        xshift,yshift, xrms, yrms = self.evaluatePos(dataTi, dataTi2)
        print("%d blindMatch stars, after trans: \nxshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(dataOi.shape[0], xshift,yshift, xrms, yrms))
    
        starPoss = stars[:,[self.xIdx, self.yIdx]]
        starPossTi = cv2.perspectiveTransform(np.array([starPoss]), h)
        starPossTi = starPossTi[0]

        xshift,yshift, xrms, yrms = self.evaluatePos(starPoss, starPossTi)
        starTrans = stars.copy()
        starTrans[:,[self.xIdx, self.yIdx]] = starPossTi
        print("%d orig stars, after trans: \nxshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(stars.shape[0], xshift,yshift, xrms, yrms))
        
        return starTrans
    
    def polynomialFitEvulate(self, dataOi, dataTi):
    
        tixp, tiyp = self.polynomialFit(dataOi, dataTi, 1)
        tp1 = tixp.parameters
        tp2 = tiyp.parameters
        
        a = tp1[0]
        b = tp1[1]
        c = tp1[2]
        d = tp2[0]
        e = tp2[1]
        f = tp2[2]
        
        xshift = a
        yshift = d
        xrotation = math.atan(e/b)*180/math.pi
        yrotation = math.atan(c/f)*180/math.pi
        #print("xshift=%.2f, yshift=%.2f, xrotation=%.5f, yrotation=%.5f"%(xshift,yshift, xrotation, yrotation))
            
        return xshift,yshift, xrotation, yrotation
            
    def polynomialFit(self, dataOi, dataTi, degree=3):
            
        oix = dataOi[:,0]
        oiy = dataOi[:,1]
        tix = dataTi[:,0]
        tiy = dataTi[:,1]
        
        p_init = models.Polynomial2D(degree)
        fit_p = fitting.LevMarLSQFitter()
        
        with warnings.catch_warnings():
            # Ignore model linearity warning from the fitter
            warnings.simplefilter('ignore')
            tixp = fit_p(p_init, oix, oiy, tix)
            tiyp = fit_p(p_init, oix, oiy, tiy)
            
        return tixp, tiyp
            
    def posTransPolynomial(self, posMchs, stars, degree=3):
        
        #print(posMchs)
        for i, tm in enumerate(posMchs):
            if i==0:
                dataOi = posMchs[i][0]
                dataTi = posMchs[i][1]
            else:
                dataOi = np.concatenate([dataOi,posMchs[i][0]])
                dataTi = np.concatenate([dataTi,posMchs[i][1]])
        
        blindStarNum = dataOi.shape[0]
        #xshift,yshift, xrms, yrms = self.evaluatePos(dataOi, dataTi)
        #print("%d blindMatch stars, before trans: xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(dataOi.shape[0], xshift,yshift, xrms, yrms))
          
        #xshift,yshift, xrotation, yrotation = 0, 0, 0, 0
        xshift,yshift, xrotation, yrotation = self.polynomialFitEvulate(dataOi, dataTi)
        #print("fitting: xshift=%.2f, yshift=%.2f, xrotation=%.5f, yrotation=%.5f"%(xshift,yshift, xrotation, yrotation))
        tixp, tiyp = self.polynomialFit(dataOi, dataTi, degree)
        
        ''' 
        oix = dataOi[:,0]
        oiy = dataOi[:,1]
        tix2 = tixp(oix, oiy)
        tiy2 = tiyp(oix, oiy)
            
        dataTi2 = np.concatenate([tix2.reshape((tix2.shape[0],1)),tiy2.reshape((tiy2.shape[0],1))],axis=1)
        xshift,yshift, xrms, yrms = self.evaluatePos(dataTi, dataTi2)
        print("%d blindMatch stars, after trans: xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(dataOi.shape[0], xshift,yshift, xrms, yrms))
        '''
        
        starPoss = stars[:,[self.xIdx, self.yIdx]]
        oix = starPoss[:,0]
        oiy = starPoss[:,1]
        tix2 = tixp(oix, oiy)
        tiy2 = tiyp(oix, oiy)
        starPossTi = np.concatenate([tix2.reshape((tix2.shape[0],1)),tiy2.reshape((tiy2.shape[0],1))],axis=1)

        #xshift,yshift, xrms, yrms = self.evaluatePos(starPoss, starPossTi)
        #print("%d orig stars, after trans: xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(stars.shape[0], xshift,yshift, xrms, yrms))
        
        starTrans = stars.copy()
        #starTrans = stars
        starTrans[:,[self.xIdx, self.yIdx]] = starPossTi
        
        return starTrans, xshift,yshift, xrotation, yrotation, blindStarNum

        
    def posTransPerspective2(self, oiMchPos, tiMchPos, stars):
        
        h, tmask = cv2.findHomography(oiMchPos, tiMchPos, cv2.RANSAC, 0.1) #0, RANSAC , LMEDS
        
        dataTi2 = cv2.perspectiveTransform(np.array([oiMchPos]), h) #calibrateCamera
        dataTi2 = dataTi2[0]
        
        starPoss = stars[:,[self.xIdx, self.yIdx]]
        starPossTi = cv2.perspectiveTransform(np.array([starPoss]), h)
        starPossTi = starPossTi[0]

        starTrans = stars.copy()
        starTrans[:,[self.xIdx, self.yIdx]] = starPossTi
        
        return starTrans
    
    def posTransPolynomial2(self, oiMchPos, tiMchPos, stars, degree=5):
        
        tixp, tiyp = self.polynomialFit(oiMchPos, tiMchPos, degree)
        
        starPoss = stars[:,[self.xIdx, self.yIdx]]
        oix = starPoss[:,0]
        oiy = starPoss[:,1]
        tix2 = tixp(oix, oiy)
        tiy2 = tiyp(oix, oiy)
        starPossTi = np.concatenate([tix2.reshape((tix2.shape[0],1)),tiy2.reshape((tiy2.shape[0],1))],axis=1)
        starTrans = stars.copy()
        starTrans[:,[self.xIdx, self.yIdx]] = starPossTi
        
        return starTrans


def imgStatistic(fname, catData, size=2000):

    imgSize = (4136, 4196)
    #imgSize = (4136, 4096)
    imgW = imgSize[1]
    imgH = imgSize[0]
    
    halfSize = size/2
    xStart = int(imgW/2 - halfSize)
    xEnd = int(imgW/2 + halfSize)
    yStart = int(imgH/2 - halfSize)
    yEnd = int(imgH/2 + halfSize)
    
    dateStr = fname[14:27] #190302T114028
    camName = fname[2:4] #23
    fwhms = []
    bkgs = []
    for row in catData:
        tx = row[0]
        ty = row[1]
        fwhm = row[9]
        bkg = row[8]
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
    
    return dateStr, camName, fwhmMean, fwhmRms, bkgMean, bkgRms
    

    
def doBlindMatch(srcDir, oiFile, tiFile):
    
    rstStr = ''
    oiMatch = BlindMatch()
    tiMatch = BlindMatch()
    
    oiData = np.loadtxt("%s/%s"%(srcDir, oiFile))
    tiData = np.loadtxt("%s/%s"%(srcDir, tiFile))
    
    dateStr, camName, fwhmMean, fwhmRms, bkgMean, bkgRms = imgStatistic(oiFile, oiData)
    #print("orign")
    #print(oiData.shape)
    #print(tiData.shape)
    
    try:
        tiXY, mchIdxsTi = tiMatch.createBlindMatchFeatures(tiData)
        
        if len(tiXY)==0:
            print("%s create feature failure"%(tiFile))
        else:
            tarray = np.array(mchIdxsTi)
            tDist = tarray[:,:,2]
            tiTree = KDTree(tDist)
            
            starttime = datetime.now()
            #createBlindMatchFeatures(self, stars, featurePoint=160, featureNum=10, searchRTimes=2, partitionNum=4)
            oiXY, mchIdxsOi = oiMatch.createBlindMatchFeatures(oiData)
            if len(mchIdxsOi)==0:
                print("%s searchR %d create feature failure, reuse %d"%(oiFile, 2, 2*2))
                oiXY, mchIdxsOi = oiMatch.createBlindMatchFeatures(oiData,searchRTimes=4)
        
            totalMatchNum = 0
            mchList = []
            mchRadius = [20,40,100]
            for mchR in mchRadius:
                for i, oIdx in enumerate(mchIdxsOi):
                    td = oIdx[:,2]
                    mchIdx = tiTree.query_ball_point(td, mchR)
                    
                    if len(mchIdx)>0:
                        for ii, tidx0 in enumerate(mchIdx):
                            tdata00 = tarray[tidx0]
                            dm, isMchOk = oiMatch.blindDistMatch(oIdx, tdata00, 1, 5)
                            if isMchOk:
                                #print("query %d KDTree match %d, precisely match %dth with %d point"%(i, len(mchIdx), ii, len(dm)))
                                #print(dm)
                                omIdx = dm[:,0]
                                tmIdx = dm[:,1]
                                oxy01 = oiXY[i]
                                txy02 = tiXY[tidx0]
                                totalMatchNum += 1
                                
                                opos = omIdx[:,0:2]
                                tpos = tmIdx[:,0:2]
                                oxy1 = np.concatenate([opos,[oxy01]])
                                txy1 = np.concatenate([tpos,[txy02]])
                                mchList.append((oxy1,txy1))
                                break
                            
                if len(mchList)>5:
                    break
                elif mchR<100:
                    mchList = []
                    print("%s radius %d matchNum %d"%(oiFile, mchR, len(mchList)))
                    
            endtime = datetime.now()
            blindMatchTime = (endtime - starttime).total_seconds()*1000
                
            if len(mchList)>1:
                #print("total Match key points %d"%(totalMatchNum))
                starOiTi, xshift,yshift, xrotation, yrotation, blindStarNum = tiMatch.posTransPolynomial(mchList, oiData,2) # posTransPolynomial posTransPerspective
                #print("fitting: xshift=%.2f, yshift=%.2f, xrotation=%.5f, yrotation=%.5f"%(xshift,yshift, xrotation, yrotation))
                #print(starOiTi.shape)
                
                mchRadius = 4
                starttime = datetime.now()
                crossMatch = CrossMatch()
                #tiData = crossMatch.filterStar(tiData)
                crossMatch.createRegionIdx(tiData)
                #crossMatch.statisticRegions()
                mchPosPairs, orgPosIdxs = crossMatch.xyMatch(starOiTi, mchRadius)
                endtime = datetime.now()
                runTime0 = (endtime - starttime).total_seconds()*1000
                mchRatios0, oiPosJoin0,tiPosJoin0, mchData0, xshift0,yshift0, xrms0, yrms0 \
                    = crossMatch.evaluateMatchResult(starOiTi, tiData, mchPosPairs)
                
                oiDataMch = oiData[orgPosIdxs]
                oiMchPos = oiDataMch[:,0:2]
                tiMchPos = mchPosPairs[:,2:4]
                starOiTiPsp2 = tiMatch.posTransPerspective2(oiMchPos, tiMchPos, oiData)
                starOiTiPly23 = tiMatch.posTransPolynomial2(oiMchPos, tiMchPos, oiData, 3)
                starOiTiPly25 = tiMatch.posTransPolynomial2(oiMchPos, tiMchPos, oiData, 5)
                
                starttime = datetime.now()
                mchPosPairs, orgPosIdxs = crossMatch.xyMatch(starOiTiPsp2, mchRadius)
                endtime = datetime.now()
                runTime1 = (endtime - starttime).total_seconds()*1000
                mchRatios1, oiPosJoin1,tiPosJoin1, mchData1, xshift1,yshift1, xrms1, yrms1 \
                    = crossMatch.evaluateMatchResult(starOiTiPsp2, tiData, mchPosPairs)

                
                starttime = datetime.now()
                mchPosPairs, orgPosIdxs = crossMatch.xyMatch(starOiTiPly23, mchRadius)
                endtime = datetime.now()
                runTime2 = (endtime - starttime).total_seconds()*1000
                mchRatios2, oiPosJoin2,tiPosJoin2, mchData2, xshift2,yshift2, xrms2, yrms2 \
                    = crossMatch.evaluateMatchResult(starOiTiPly23, tiData, mchPosPairs)
                
                starttime = datetime.now()
                mchPosPairs, orgPosIdxs = crossMatch.xyMatch(starOiTiPly25, mchRadius)
                endtime = datetime.now()
                runTime3 = (endtime - starttime).total_seconds()*1000
                mchRatios3, oiPosJoin3,tiPosJoin3, mchData3, xshift3,yshift3, xrms3, yrms3 \
                    = crossMatch.evaluateMatchResult(starOiTiPly25, tiData, mchPosPairs)
                
                rstStr = "%s %.2f %.2f %.2f %.2f %d %d "\
                    "%d %d "\
                    "%d %d %d %.2f %.2f %.2f %.2f %.2f %d "\
                    "%d %d %d %.2f %.2f %.2f %.2f %.2f %d "\
                    "%d %d %d %.2f %.2f %.2f %.2f %.2f %d "\
                    "%s %s %.2f %.2f %.2f %.2f %d "\
                    "%d %d %d %.2f %.2f %.2f %.2f %.2f %d \n"\
                    %(oiFile, xshift,yshift, xrotation, yrotation, blindStarNum, totalMatchNum, \
                      tiData.shape[0], oiData.shape[0], \
                      oiPosJoin0,tiPosJoin0, mchData0, mchRatios0, xshift0,yshift0, xrms0, yrms0,runTime0,\
                      oiPosJoin1,tiPosJoin1, mchData1, mchRatios1, xshift1,yshift1, xrms1, yrms1,runTime1,\
                      oiPosJoin2,tiPosJoin2, mchData2, mchRatios2, xshift2,yshift2, xrms2, yrms2,runTime2,\
                      dateStr, camName, fwhmMean, fwhmRms, bkgMean, bkgRms, blindMatchTime,\
                      oiPosJoin3,tiPosJoin3, mchData3, mchRatios3, xshift3,yshift3, xrms3, yrms3,runTime3)
                #print(rstStr)
            
    except Exception as e:
        print("blind match error")
        tstr = traceback.format_exc()
        print(tstr)
    if len(rstStr)==0:
        rstStr = "%s %.2f %.2f %.2f %.2f %d %d "\
            "%d %d "\
            "%d %d %d %.2f %.2f %.2f %.2f %.2f %d "\
            "%d %d %d %.2f %.2f %.2f %.2f %.2f %d "\
            "%d %d %d %.2f %.2f %.2f %.2f %.2f %d "\
            "%s %s %.2f %.2f %.2f %.2f %d "\
            "%d %d %d %.2f %.2f %.2f %.2f %.2f %d \n"\
            %(oiFile, 0,0, 0, 0, 0, 0, \
              tiData.shape[0], oiData.shape[0], \
              0,0, 0, 0, 0,0, 0, 0,0,\
              0,0, 0, 0, 0,0, 0, 0,0,\
              0,0, 0, 0, 0,0, 0, 0,0,\
              dateStr, camName, fwhmMean, fwhmRms, bkgMean, bkgRms, 0,\
              0,0, 0, 0, 0,0, 0, 0,0)
    return rstStr

def test():
    

    srcDir = "/data/gwac_diff_xy/matchTest/cat"
    dstDir = "/data/gwac_diff_xy/matchTest/tmp"
    
    tmplCat0 = ['G021_mon_objt_181101T17255569.cat',
                'G032_mon_objt_190110T14080401.cat',
                'G043_mon_objt_190126T10594812.cat',
                'G024_mon_objt_181018T18570151.cat']
    
    objCats = os.listdir(srcDir)
    
    for tmplCat in tmplCat0:
        print("\n*****************************\n")
        print("temp %s match..."%(tmplCat))
        tmplCCDNum = tmplCat[3]
        
        savePath1 = "%s/%s_mch_statistic4000d3r4.cat"%(dstDir,tmplCat.split('.')[0])
        tf1 = open(savePath1, 'w')
        #tf.write("#fname, starNum, featureNum, matchNum, micro seconds\n")
        
        #G021_mon_objt_181101T17255569.cat
        for objCat in objCats:
            ccdNum = objCat[3]
            if ccdNum == tmplCCDNum and tmplCat!=objCat:
                print("match %s"%(objCat))
                tstr = doBlindMatch(srcDir, objCat, tmplCat)
                tf1.write(tstr)
                tf1.flush()
        tf1.close()
        
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021 &
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python BatchDiff.py G021
if __name__ == "__main__":
        
    test()