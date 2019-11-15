# -*- coding: utf-8 -*-
import numpy as np
import math
import cv2
import matplotlib.pyplot as plt
import warnings
from datetime import datetime
from astropy.modeling import models, fitting
            
class CrossMatch(object):
    
    def __init__(self, imgW=4096, imgH=4136): 
        self.imgW = imgW
        self.imgH = imgH
        #regionBorder=[minX,maxX,minY,maxY]
        self.regionBorder=[10,self.imgW-10,10,self.imgH-10]
        #self.regionBorder=[0,4096,0,4136]
        
        self.magIdx = 11
        self.xIdx = 0
        self.yIdx = 1
        
        self.regNum = 0
        self.regSize = 0
        self.regW = 0
        self.regH = 0
         
    def getLineDistance(self, star1, star2):
        
        tx = star1[0] - star2[0]
        ty = star1[1] - star2[1]
        tdist = math.sqrt(tx*tx+ty*ty)
        return tdist
    
    def getBright(self, tdata, brightStarNumPercentage=0.05, partitionNum=4, darkStarNum=2000):
        
        brightStarMin=16
        brightStarMax=160
        totalNum = tdata.shape[0]
        brightStarNum = totalNum*brightStarNumPercentage
        if brightStarNum<brightStarMin:
            brightStarNum=brightStarMin
        elif brightStarNum>brightStarMax:
            brightStarNum=brightStarMax
        
        pBrightStarNum = math.ceil(brightStarNum/(partitionNum*partitionNum))
        pDarkStarNum = math.ceil(darkStarNum/(partitionNum*partitionNum))
        
        regions = self.partition(tdata, pNum=partitionNum)
        
        brightStars = np.array([])
        otherStars = np.array([])
        for treg in regions:
            tregData = np.array(treg)
            if tregData.shape[0]==0:
                continue
            sortMag = tregData[tregData[:,self.magIdx].argsort()]
            if brightStars.shape[0]==0:
                brightStars = sortMag[:pBrightStarNum]
                otherStars = sortMag[pBrightStarNum:pDarkStarNum]
                #otherStars = sortMag[pBrightStarNum:]
            else:
                brightStars = np.concatenate([brightStars,sortMag[:pBrightStarNum]])
                otherStars = np.concatenate([otherStars,sortMag[pBrightStarNum:pDarkStarNum]])
        
        return brightStars, otherStars
    
    def filterStar(self, tdata):
        
        condition1 = (tdata[:,self.xIdx]>=self.regionBorder[0]) & (tdata[:,self.xIdx]<=self.regionBorder[1]) & \
            (tdata[:,self.yIdx]>=self.regionBorder[2]) & (tdata[:,self.yIdx]<=self.regionBorder[3])
        tdata2 = tdata[condition1]
        
        return tdata2
    
    def partition(self, oiData, pNum=4):
        
        regSize = pNum
        regW = (self.regionBorder[1] - self.regionBorder[0])*1.0/regSize
        regH = (self.regionBorder[3] - self.regionBorder[2])*1.0/regSize
        
        regionPos = []
        for i in range(regSize*regSize):
            regionPos.append([])
        
        for tdata in oiData:
            x = tdata[self.xIdx]
            y = tdata[self.yIdx]
            if x>=self.regionBorder[0] and x<=self.regionBorder[1] and y>=self.regionBorder[2] and y<=self.regionBorder[3]:
                regIdx = self.getRegionIdx_(x,y, regW, regH, regSize)
                regionPos[regIdx].append(tdata)
        
        return regionPos
    
    def createRegionIdx(self, tdata, minRegionStarNum=10):
        
        pos = tdata[:,[self.xIdx, self.yIdx]]
        
        totalNum = pos.shape[0]
        #print("totalNum=%d"%(totalNum))
        self.regNum = math.floor(totalNum/minRegionStarNum)
        self.regSize = math.floor(math.sqrt(self.regNum))
        self.regW = (self.regionBorder[1] - self.regionBorder[0])*1.0/self.regSize
        self.regH = (self.regionBorder[3] - self.regionBorder[2])*1.0/self.regSize
        
        regionStarNum = []
        regionPos = []
        for i in range(self.regSize*self.regSize):
            regionPos.append([])
            regionStarNum.append(0)
        
        for tp in pos:
            x = tp[0]
            y = tp[1]
            if x>=self.regionBorder[0] and x<=self.regionBorder[1] and y>=self.regionBorder[2] and y<=self.regionBorder[3]:
                regIdx = self.getRegionIdx(x,y)
                regionPos[regIdx].append((x,y))
                regionStarNum[regIdx] += 1
        
        self.regionPos = regionPos
        self.regionStarNum = regionStarNum
    
    def getRegionIdx(self, x,y):
        
        return self.getRegionIdx_(x,y, self.regW, self.regH, self.regSize)
    
    def getRegionIdx_(self, x,y, regW, regH, regSize):
    
        regX = math.floor((x-self.regionBorder[0])/regW)
        regY = math.floor((y-self.regionBorder[2])/regH)
        if regX<0:
            regX=0
        elif regX>=regSize:
            regX = regSize-1
        if regY<0:
            regY=0
        elif regY>=regSize:
            regY = regSize-1
        regIdx = regY*regSize+regX
        
        return regIdx
    
    def statisticRegions(self):
        
        tnum = 0
        for tr in self.regionPos:
            tnum += len(tr)
        
        tnum2 = 0
        for trn in self.regionStarNum:
            tnum2 += trn
        
        print("region star count=%d, region num sum=%d"%(tnum, tnum2))
    
    def getSearchRegions(self, x, y, searchRadius):
        
        #searchRadius = self.regSize*2
        
        minx = x - searchRadius
        maxx = x + searchRadius
        miny = y - searchRadius
        maxy = y + searchRadius
        
        minRegX = math.floor((minx-self.regionBorder[0])/self.regW)
        minRegY = math.floor((miny-self.regionBorder[2])/self.regH)
        maxRegX = math.floor((maxx-self.regionBorder[0])/self.regW)
        maxRegY = math.floor((maxy-self.regionBorder[2])/self.regH)
        if minRegX<0:
            minRegX=0
        elif minRegX>=self.regSize:
            minRegX = self.regSize-1
        if minRegY<0:
            minRegY=0
        elif minRegY>=self.regSize:
            minRegY = self.regSize-1
        if maxRegX<0:
            maxRegX=0
        elif maxRegX>=self.regSize:
            maxRegX = self.regSize-1
        if maxRegY<0:
            maxRegY=0
        elif maxRegY>=self.regSize:
            maxRegY = self.regSize-1
            
        regIdxs = []
        for ty in range(minRegY, maxRegY+1):
            for tx in range(minRegX, maxRegX+1):
                tidx = ty*self.regSize + tx
                regIdxs.append(tidx)
        
        return regIdxs

        
    def getNearestN(self, x,y, searchRadius, nNum=1):
        
        regIdxs = self.getSearchRegions(x, y, searchRadius)
        
        stars = []
        for rid in regIdxs:
            stars.extend(self.regionPos[rid])
            
        tdistances = []
        for tstar in stars:
            tdist = self.getLineDistance((x,y),tstar)
            tdistances.append((tstar[0], tstar[1], tdist))
            
        tdistances = np.array(tdistances) 
        if len(tdistances.shape)==2 and tdistances.shape[0]>0:
            #print(tdistances.shape)
            tdistances = tdistances[tdistances[:,2].argsort()]
            tdistances = tdistances[:nNum]
        
        return tdistances
    
    
    def searchR(self, x,y, searchRadius):
        
        regIdxs = self.getSearchRegions(x, y, searchRadius)
        
        stars = []
        for rid in regIdxs:
            stars.extend(self.regionPos[rid])
            
        tdistances = []
        for tstar in stars:
            tdist = self.getLineDistance((x,y),tstar)
            if tdist<searchRadius:
                tdistances.append((tstar[0], tstar[1], tdist))
            
        tdistances = np.array(tdistances) 
        if len(tdistances.shape)==2 and tdistances.shape[0]>0:
            #print(tdistances.shape)
            tdistances = tdistances[tdistances[:,2].argsort()]
            tdistances = tdistances[0]
        
        return tdistances
    
    def xyMatch(self, stars, searchRadius = 1):
        
        orgPosIdxs = []
        tXY = []
        mchIdxs = []
        for i, ts in enumerate(stars):
            x = ts[self.xIdx]
            y = ts[self.yIdx]
            nN = self.searchR(x,y, searchRadius)
            if nN.shape[0]>0:
                tXY.append((x,y))
                mchIdxs.append(nN)
                orgPosIdxs.append(i)
        
        tXY = np.array(tXY)
        mchIdxs = np.array(mchIdxs)
        
        mchPosPairs = np.concatenate([tXY,mchIdxs[:,0:2]], axis=1)
        return mchPosPairs, orgPosIdxs
    
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
      
    def evaluateMatchResult(self, oiData, tiData, mchData):
        
        pos1 = mchData[:,0:2]
        pos2 = mchData[:,2:4]
        xshift,yshift, xrms, yrms = self.evaluatePos(pos1, pos2, True)
        
        oiPos = oiData[:,[self.xIdx, self.yIdx]]
        tiPos = tiData[:,[self.xIdx, self.yIdx]]
        
        oiMinXY = np.min(oiPos, axis=0)
        oiMaxXY = np.max(oiPos, axis=0)
        tiMinXY = np.min(tiPos, axis=0)
        tiMaxXY = np.max(tiPos, axis=0)
        
        if oiMinXY[0] > tiMinXY[0] :
            minX = oiMinXY[0]
        else:
            minX = tiMinXY[0]
            
        if oiMinXY[1] > tiMinXY[1] :
            minY = oiMinXY[1]
        else:
            minY = tiMinXY[1]
            
        if oiMaxXY[0] < tiMaxXY[0] :
            maxX = oiMaxXY[0]
        else:
            maxX = tiMaxXY[0]
            
        if oiMaxXY[1] < tiMaxXY[1] :
            maxY = oiMaxXY[1]
        else:
            maxY = tiMaxXY[1]
            
        oiPosJoin = oiPos[(oiPos[:,0]>=minX) & (oiPos[:,0]<=maxX) & (oiPos[:,1]>=minY) & (oiPos[:,1]<=maxY)]
        tiPosJoin = tiPos[(tiPos[:,0]>=minX) & (tiPos[:,0]<=maxX) & (tiPos[:,1]>=minY) & (tiPos[:,1]<=maxY)]
        
        #print("oi:%d, ti:%d, joinOi:%d, joinTi:%d, mch:%d"\
        #      %(oiPos.shape[0],tiPos.shape[0],oiPosJoin.shape[0],tiPosJoin.shape[0], mchData.shape[0]))
        #print("xmean=%.2f, ymean=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))   
        
        joinNum = oiPosJoin.shape[0] if oiPosJoin.shape[0]<tiPosJoin.shape[0] else tiPosJoin.shape[0]
        mchRatios = mchData.shape[0]*100.0/joinNum
        
        return mchRatios, oiPosJoin.shape[0],tiPosJoin.shape[0], mchData.shape[0], xshift,yshift, xrms, yrms
    
def test():
    
    srcDir = 'data'
    oiFile = 'G041_mon_objt_181018T17592546.cat'
    tiFile = 'G021_mon_objt_181101T17255569.cat'
    
    oiData = np.loadtxt("%s/%s"%(srcDir, oiFile))
    #tiData = np.loadtxt("%s/%s"%(srcDir, tiFile))
    print("orign")
    print(oiData.shape)
    #print(tiData.shape)
    
    oiMatch = CrossMatch()
    oiMatch.createRegionIdx(oiData)
    oiMatch.statisticRegions()
    
    print(oiData.shape)
    starttime = datetime.now()
    mchPosPairs = oiMatch.xyMatch(oiData, 1)
    print("origNum:%d, after:%d"%(oiData.shape[0],mchPosPairs.shape[0]))
    endtime = datetime.now()
    runTime = (endtime - starttime).total_seconds()*1000
    print("********** rematch %s use %d micro seconds"%(oiFile, runTime))
    
if __name__ == "__main__":
        
    test()