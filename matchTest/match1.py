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
        #self.regionBorder=[0,4096,0,4136]
        '''
        self.regNum = 0
        self.regSize = 0
        self.regW = 0
        self.regH = 0
        '''    
    def getRegionIdx(self, x,y, regNum, regSize, regW, regH):
    
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
                
    def createRegionIdx(self, tdata, minRegionStarNum=10):
        
        pos = tdata[:,3:5]
        
        totalNum = pos.shape[0]
        regNum = math.floor(totalNum/minRegionStarNum)
        regSize = math.floor(math.sqrt(regNum))
        regW = (self.regionBorder[1] - self.regionBorder[0])*1.0/regSize
        regH = (self.regionBorder[3] - self.regionBorder[2])*1.0/regSize
        
        regionStarNum = []
        regionPos = []
        for i in range(regSize*regSize):
            regionPos.append([])
            regionStarNum.append(0)
        
        for tp in pos:
            x = tp[0]
            y = tp[1]
            if x>=self.regionBorder[0] and x<=self.regionBorder[1] and y>=self.regionBorder[2] and y<=self.regionBorder[3]:
                regIdx = self.getRegionIdx(x,y, regNum, regSize, regW, regH)
                regionPos[regIdx].append((x,y))
                regionStarNum[regIdx] += 1
        
        return regionPos, regionStarNum, regNum, regSize, regW, regH
    
    def getBright(self, tdata, starNum=100):
        
        mag = tdata[:,38]
        mag = np.sort(mag)
        maxMag = mag[starNum-1]
        brightStar = tdata[tdata[:,38]<=maxMag]
        darkStar = tdata[tdata[:,38]>maxMag]
        
        return brightStar, darkStar
    
    def filterStar(self, tdata):
        
        condition1 = (tdata[:,3]>=self.regionBorder[0]) & (tdata[:,3]<=self.regionBorder[1]) & \
            (tdata[:,4]>=self.regionBorder[2]) & (tdata[:,4]<=self.regionBorder[3])
        tdata = tdata[condition1]
        
        return tdata
    
    def getSearchRegions(self, x, y, regNum, regSize, regW, regH):
        
        searchRadius = regSize*2
        x = x-self.regionBorder[0]
        y = y-self.regionBorder[2]
        
        minx = x - searchRadius
        maxx = x + searchRadius
        miny = y - searchRadius
        maxy = y + searchRadius
        
        minRegX = math.floor((minx-self.regionBorder[0])/regW)
        minRegY = math.floor((miny-self.regionBorder[2])/regH)
        maxRegX = math.floor((maxx-self.regionBorder[0])/regW)
        maxRegY = math.floor((maxy-self.regionBorder[2])/regH)
        if minRegX<0:
            minRegX=0
        elif minRegX>=regSize:
            minRegX = regSize-1
        if minRegY<0:
            minRegY=0
        elif minRegY>=regSize:
            minRegY = regSize-1
        if maxRegX<0:
            maxRegX=0
        elif maxRegX>=regSize:
            maxRegX = regSize-1
        if maxRegY<0:
            maxRegY=0
        elif maxRegY>=regSize:
            maxRegY = regSize-1
            
        regIdxs = []
        for ty in range(minRegY, maxRegY+1):
            for tx in range(minRegX, maxRegX+1):
                tidx = ty*regSize + tx
                regIdxs.append(tidx)
        
        return regIdxs

    def getLineDistance(self, star1, star2):
        
        tx = star1[0] - star2[0]
        ty = star1[1] - star2[1]
        tdist = math.sqrt(tx*tx+ty*ty)
        return tdist
        
    def getNearestN(self, x,y, regionPos, regNum, regSize, regW, regH, num=10):
        
        regIdxs = self.getSearchRegions(x, y, regNum, regSize, regW, regH)
        print(regIdxs)
        
        stars = []
        for rid in regIdxs:
            stars.extend(regionPos[rid])
            
        tdistances = []
        for tstar in stars:
            tdist = self.getLineDistance((x,y),tstar)
            tdistances.append((tstar[0], tstar[1], tdist))
        
        tdistances = np.array(tdistances)
        tdistances = tdistances[tdistances[:,2].argsort()]
        
        return tdistances[:num]
    
    def createMatchIdx(self, stars, regionPos, regNum, regSize, regW, regH):
        
        mchIdxs = []
        for i, ts in enumerate(stars):
            x = ts[3]
            y = ts[4]
            if i==68:
                print('star %d, x %f, y %f'%(i,x,y))
            nN = self.getNearestN(x,y, regionPos, regNum, regSize, regW, regH)
            mchIdxs.append(nN)
        
        return mchIdxs
        
        
    def match(self, srcDir, oiFile, tiFile):
                  
        oiData = np.loadtxt("%s/%s"%(srcDir, oiFile))
        tiData = np.loadtxt("%s/%s"%(srcDir, tiFile))
        print(oiData.shape)
        print(tiData.shape)
        
        oiData = self.filterStar(oiData)
        tiData = self.filterStar(tiData)
        
        brightStarTi, darkStarTi = self.getBright(tiData)
        brightStarOi, darkStarOi = self.getBright(oiData)
        
        regionPosTi, regionStarNumTi, regNumTi, regSizeTi, regWTi, regHTi = self.createRegionIdx(darkStarTi)
        regionPosOi, regionStarNumOi, regNumOi, regSizeOi, regWOi, regHOi = self.createRegionIdx(darkStarOi)
        
        mchIdxsTi = self.createMatchIdx(brightStarTi, regionPosTi, regNumTi, regSizeTi, regWTi, regHTi)
        mchIdxsOi = self.createMatchIdx(brightStarOi, regionPosOi, regNumOi, regSizeOi, regWOi, regHOi)
            

def test():
    
    tpath = 'data'
    tfile1 = 'G031_mon_objt_190116T21430226.cat'
    tfile2 = 'G041_mon_objt_190101T21551991.cat'
    
    starMatch = StarMatch()
    starMatch.match(tpath, tfile1, tfile2)
    
if __name__ == "__main__":
        
    test()
    