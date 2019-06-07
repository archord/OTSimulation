# -*- coding: utf-8 -*-
import numpy as np
import os
import math

            
class StarMatch(object):
    
    def __init__(self): 
        self.imgW = 4096
        self.imgH = 4136
        #regionBorder=[minY,maxY,minX,maxX]
        self.regionBorder=[100,4000,100,4000]
        
        self.regNum = 0
        self.regSize = 0
        self.regW = 0
        self.regH = 0
        
        self.regionStarNum = []
        self.regionPos = []
            
    def getRegionIdx(self, x,y):
    
        regX = math.floor((x-self.regionBorder[0])/self.regW)
        regY = math.floor((y-self.regionBorder[2])/self.regH)
        if regX<0:
            regX=0
        elif regX>=self.regSize:
            regX = self.regSize-1
        if regY<0:
            regY=0
        elif regY>=self.regSize:
            regY = self.regSize-1
        regIdx = regY*self.regSize+regX
        
        return regIdx
                
    def createRegionIdx(self, tdata, minRegionStarNum=10):
        
        pos = tdata[:,3:5]
        
        totalNum = pos.shape[0]
        self.regNum = math.floor(totalNum/minRegionStarNum)
        self.regSize = math.floor(math.sqrt(self.regNum))
        self.regW = (self.regionBorder[1] - self.regionBorder[0])*1.0/self.regSize
        self.regH = (self.regionBorder[3] - self.regionBorder[2])*1.0/self.regSize
        
        for i in self.regSize*self.regSize:
            self.regionPos.append([])
            self.regionStarNum.append(0)
        
        for tp in pos:
            x = tp[0]
            y = tp[1]
            if x>=self.regionBorder[0] and x<=self.regionBorder[1] and y>=self.regionBorder[2] and y<=self.regionBorder[3]:
                regIdx = self.getRegionIdx(x,y)
                self.regionPos[regIdx].append((x,y))
                self.regionStarNum[regIdx] += 1
                
    
    def getBright(self, tdata, starNum=100):
        
        mag = tdata[:,38]
        mag = np.sort(mag)
        maxMag = mag[starNum-1]
        tdata = tdata[tdata[:,38]<maxMag]
        
        return tdata
    
    def filterStar(self, tdata):
        
        condition1 = tdata[:,3]>=self.regionBorder[0] & tdata[:,3]<=self.regionBorder[1] & \
            tdata[:,4]>=self.regionBorder[2] & tdata[:,4]<=self.regionBorder[3]
        tdata = tdata[condition1]
        
        return tdata
    
    def getSearchRegions(self, x, y):
        
        searchRadius = self.regSize*2
        
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

    def getLineDistance(self, star1, star2):
        
        tx = star1[0] - star2[0]
        ty = star1[1] - star2[1]
        tdist = math.sqrt(tx*tx+ty*ty)
        return tdist
        
    def getNearestN(self, x,y, num=10):
        
        regIdxs = self.getSearchRegions(x, y)
        
        stars = []
        for rid in regIdxs:
            stars.extend(self.regionPos[rid])
            
        tdistances = []
        for tstar in stars:
            tdist = self.getLineDistance((x,y),tstar)
            tdistances.append((tstar[0], tstar[1], tdist))
        
        tdistances = np.array(tdistances)
        tdistances = tdistances[tdistances[:,2].argsort()]
        
        return tdistances[:num]
    
    def createMatchIdx(self, stars):
        
        for ts in stars:
            x = ts[3]
            y = ts[4]
            regIdx = self.getRegionIdx(x,y)
        
        
    def match(self, srcDir, oiFile, tiFile):
                  
        oiData = np.loadtxt("%s/%s"%(srcDir, oiFile))
        tiData = np.loadtxt("%s/%s"%(srcDir, tiFile))
        
        oiData = self.filterStar(oiData)
        tiData = self.filterStar(tiData)
        
        regionPosOi, regionStarNumOi = self.createRegionIdx(oiData)
        regionPosTi, regionStarNumTi = self.createRegionIdx(tiData)
        
        brightStarOi = self.getBright(oiData)
        brightStarTi = self.getBright(tiData)

def test():
    
    tpath = 'data'
    tfile1 = 'G031_mon_objt_190116T21430226.cat'
    tfile2 = 'G041_mon_objt_190101T21551991.cat'
    
    match(tpath, tfile1, tfile2)
    
if __name__ == "__main__":
        
    test()
    