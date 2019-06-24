# -*- coding: utf-8 -*-
import numpy as np
import math
import cv2
import matplotlib.pyplot as plt
import warnings
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
    
    def createBlindMatchFeatures(self, stars, num=10, searchRTimes=2):
        
        
        oiMatch = CrossMatch()
        oiData = oiMatch.filterStar(stars)
        brightStarOi, darkStarOi = oiMatch.getBright(oiData, 100, 6000)
        oiMatch.createRegionIdx(darkStarOi)
        oiMatch.statisticRegions()
        
        searchRadius = oiMatch.regSize*searchRTimes
        
        tXY = []
        mchIdxs = []
        for i, ts in enumerate(brightStarOi):
            x = ts[0]
            y = ts[1]
            nN = oiMatch.getNearestN(x,y, searchRadius,num)
            if len(nN)==num:
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
        stars[:,[self.xIdx, self.yIdx]] = starPossTi
        print("%d orig stars, after trans: \nxshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(stars.shape[0], xshift,yshift, xrms, yrms))
        
        return stars
    
    def posTransPolynomial(self, posMchs, stars):
        
        #print(posMchs)
        for i, tm in enumerate(posMchs):
            if i==0:
                dataOi = posMchs[i][0]
                dataTi = posMchs[i][1]
            else:
                dataOi = np.concatenate([dataOi,posMchs[i][0]])
                dataTi = np.concatenate([dataTi,posMchs[i][1]])
        
        xshift,yshift, xrms, yrms = self.evaluatePos(dataOi, dataTi)
        print("%d blindMatch stars, before trans: xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(dataOi.shape[0], xshift,yshift, xrms, yrms))
        '''
        minLen = dataTi.shape[0]
        if minLen>dataOi.shape[0]:
            minLen=dataOi.shape[0]
        
        dataTi2 = dataTi[:minLen]
        dataOi2 = dataOi[:minLen]
        '''
        dataTi2 = dataTi
        dataOi2 = dataOi
        
        oix = dataOi2[:,0]
        oiy = dataOi2[:,1]
        tix = dataTi2[:,0]
        tiy = dataTi2[:,1]
        
        p_init = models.Polynomial2D(degree=3)
        fit_p = fitting.LevMarLSQFitter()
        
        with warnings.catch_warnings():
            # Ignore model linearity warning from the fitter
            warnings.simplefilter('ignore')
            tixp = fit_p(p_init, oix, oiy, tix)
            tiyp = fit_p(p_init, oix, oiy, tiy)
            
            tix2 = tixp(oix, oiy)
            tiy2 = tiyp(oix, oiy)
        
        dataTi2 = np.concatenate([tix2.reshape((tix2.shape[0],1)),tiy2.reshape((tix2.shape[0],1))],axis=1)
        xshift,yshift, xrms, yrms = self.evaluatePos(dataTi, dataTi2)
        print("%d blindMatch stars, after trans: xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(dataOi.shape[0], xshift,yshift, xrms, yrms))
    
        starPoss = stars[:,[self.xIdx, self.yIdx]]
        oix = starPoss[:,0]
        oiy = starPoss[:,1]
        tix2 = tixp(oix, oiy)
        tiy2 = tiyp(oix, oiy)
        starPossTi = np.concatenate([tix2.reshape((tix2.shape[0],1)),tiy2.reshape((tix2.shape[0],1))],axis=1)

        xshift,yshift, xrms, yrms = self.evaluatePos(starPoss, starPossTi)
        stars[:,[self.xIdx, self.yIdx]] = starPossTi
        print("%d orig stars, after trans: xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(stars.shape[0], xshift,yshift, xrms, yrms))
        
        
        return stars

    
def doAll(srcDir, oiFile, tiFile):
      
    oiMatch = BlindMatch()
    tiMatch = BlindMatch()
    
    oiData = np.loadtxt("%s/%s"%(srcDir, oiFile))
    tiData = np.loadtxt("%s/%s"%(srcDir, tiFile))
    print("orign")
    print(oiData.shape)
    print(tiData.shape)
    
    tiXY, mchIdxsTi = tiMatch.createBlindMatchFeatures(tiData)
    oiXY, mchIdxsOi = oiMatch.createBlindMatchFeatures(oiData)
    
    if len(tiXY)==0:
        print("%s create feature failure"%(tiFile))
    elif len(oiXY)==0:
        print("%s create feature failure"%(oiFile))
    else:
        tarray = np.array(mchIdxsTi)
        tDist = tarray[:,:,2]
        tiTree = KDTree(tDist)
        
        totalMatchNum = 0
        mchList = []
        for i, oIdx in enumerate(mchIdxsOi):
            td = oIdx[:,2]
            mchIdx = tiTree.query_ball_point(td, 20)
            
            if len(mchIdx)>0:
                for ii, tidx0 in enumerate(mchIdx):
                    tdata00 = tarray[tidx0]
                    dm, isMchOk = oiMatch.blindDistMatch(oIdx, tdata00)
                    if isMchOk:
                        print("query %d KDTree match %d, precisely match %dth with %d point"%(i, len(mchIdx), ii, len(dm)))
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
                        
                        '''  
                        ox1 = omIdx[:,0]
                        oy1 = omIdx[:,1]
                        tx2 = tmIdx[:,0]
                        ty2 = tmIdx[:,1]
                        oiMatch.plotBlindMatch(oxy01[0],oxy01[1],ox1,oy1,txy02[0],txy02[1],tx2,ty2)
                        '''
                        break
                
        if len(mchList)>1:
            print("totalMatchNum=%d"%(totalMatchNum))
            starOiTi = tiMatch.posTransPolynomial(mchList, oiData) # posTransPolynomial posTransPerspective
            print(starOiTi.shape)
            
            starttime = datetime.now()
            crossMatch = CrossMatch()
            #tiData = crossMatch.filterStar(tiData)
            crossMatch.createRegionIdx(tiData)
            crossMatch.statisticRegions()
            mchPosPairs = crossMatch.xyMatch(starOiTi, 2)
            endtime = datetime.now()
            runTime = (endtime - starttime).total_seconds()*1000
            print("********** rematch %s use %d micro seconds"%(oiFile, runTime))
            
            crossMatch.evaluateMatchResult(starOiTi, tiData, mchPosPairs)
            
            mchPosPairs[:,0] = mchPosPairs[:,0] + 20
            mchPosPairs[:,2] = mchPosPairs[:,2] + 20
            tiMatch.saveReg(mchPosPairs[:,0:2], "data/OiMch.reg", radius=4, width=1, color='green')
            tiMatch.saveReg(mchPosPairs[:,2:4], "data/TiMch.reg", radius=4, width=1, color='red')
            
def test():
    
    tpath = 'data'
    #tfile1 = 'G031_mon_objt_190116T21430226.cat'
    #tfile2 = 'G041_mon_objt_190101T21551991.cat'
    tfile1 = 'G041_mon_objt_181018T17592546.cat' #G021_mon_objt_181106T17045393.cat G041_mon_objt_181018T17592546
    tfile2 = 'G021_mon_objt_181101T17255569.cat'
    
    doAll(tpath, tfile1, tfile2)
    
if __name__ == "__main__":
        
    test()