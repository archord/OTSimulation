# -*- coding: utf-8 -*-
import numpy as np
import os
import math
import cv2
from scipy.spatial import KDTree
import matplotlib.pyplot as plt
import warnings
from astropy.modeling import models, fitting
            
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
        
        pos = tdata[:,0:2]
        
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
    
    def statisticRegions(self,regionPos, regionStarNum):
        
        tnum = 0
        for tr in regionPos:
            tnum += len(tr)
        
        tnum2 = 0
        for trn in regionStarNum:
            tnum2 += trn
        
        print("num1=%d, num2=%d"%(tnum, tnum2))
    
    def getBright(self, tdata, starNum=100, magIdx=38):
        
        mag = tdata[:,magIdx]
        mag = np.sort(mag)
        maxMag = mag[starNum-1]
        brightStar = tdata[tdata[:,magIdx]<=maxMag]
        darkStar = tdata[tdata[:,magIdx]>maxMag]
        
        return brightStar, darkStar
    
    def filterStar(self, tdata, xIdx=3, yIdx=4):
        
        condition1 = (tdata[:,xIdx]>=self.regionBorder[0]) & (tdata[:,xIdx]<=self.regionBorder[1]) & \
            (tdata[:,yIdx]>=self.regionBorder[2]) & (tdata[:,yIdx]<=self.regionBorder[3])
        tdata = tdata[condition1]
        
        return tdata
    
    def getSearchRegions(self, x, y, searchRadius, regNum, regSize, regW, regH):
        
        #searchRadius = regSize*2
        #x = x-self.regionBorder[0]
        #y = y-self.regionBorder[2]
        
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
        
    def getNearestN(self, x,y, searchRadius, regionPos, regNum, regSize, regW, regH, num=10):
        
        regIdxs = self.getSearchRegions(x, y, searchRadius, regNum, regSize, regW, regH)
        #print(regIdxs)
        
        stars = []
        for rid in regIdxs:
            stars.extend(regionPos[rid])
            
        tdistances = []
        for tstar in stars:
            tdist = self.getLineDistance((x,y),tstar)
            tdistances.append((tstar[0], tstar[1], tdist))
            
        tdistances = np.array(tdistances)
        '''
        tpos=(2012.68,2616.21)
        #tpos=(2095.35,2531.6)
        if(self.getLineDistance((x,y),tpos)<1):
            print("***************************")
            print(regIdxs)
            print(len(stars))
            print(tdistances.shape)
            ds9RegionName = "data/star21.reg"
            self.saveReg(stars, ds9RegionName, radius=8, width=2, color='yellow')
        tpos=(2095.35,2531.6)
        if(self.getLineDistance((x,y),tpos)<1):
            print("***************************")
            print(regIdxs)
            print(len(stars))
            print(tdistances.shape)
            ds9RegionName = "data/star22.reg"
            self.saveReg(stars, ds9RegionName, radius=8, width=2, color='yellow')
        '''    
        if len(tdistances.shape)==2 and tdistances.shape[0]>0:
            #print(tdistances.shape)
            tdistances = tdistances[tdistances[:,2].argsort()]
            tdistances = tdistances[:num]
        
        
        return tdistances
    
    def searchR(self, x,y, searchRadius, regionPos, regNum, regSize, regW, regH):
        
        regIdxs = self.getSearchRegions(x, y, searchRadius, regNum, regSize, regW, regH)
        #print(regIdxs)
        
        stars = []
        for rid in regIdxs:
            stars.extend(regionPos[rid])
            
        tdistances = []
        for tstar in stars:
            tdist = self.getLineDistance((x,y),tstar)
            if tdist<=searchRadius:
                tdistances.append((tstar[0], tstar[1], tdist))
        
        tdistances = np.array(tdistances)
        if tdistances.shape[0]>0:
            tdistances = tdistances[tdistances[:,2].argsort()]
            tdistances = tdistances[0]
        
        return tdistances
    
    def createMatchIdx(self, stars, regionPos, regNum, regSize, regW, regH, num=10, searchRTimes=2):
        
        searchRadius = regSize*searchRTimes
        
        tXY = []
        mchIdxs = []
        for i, ts in enumerate(stars):
            x = ts[0]
            y = ts[1]
            #if i==68:
            #    print('star %d, x %f, y %f'%(i,x,y))
            #oi:(2043.46,2548.93), ti:(2095.35, 2531.6)
            nN = self.getNearestN(x,y, searchRadius, regionPos, regNum, regSize, regW, regH,num)
            if len(nN)==num:
                tXY.append((x,y))
                mchIdxs.append(nN)
        
        return tXY, mchIdxs
    
    def match(self, stars, regionPos, regNum, regSize, regW, regH, searchRadius = 1):
        
        
        tXY = []
        mchIdxs = []
        for i, ts in enumerate(stars):
            x = ts[0]
            y = ts[1]
            #if i==68:
            #    print('star %d, x %f, y %f'%(i,x,y))
            nN = self.searchR(x,y, searchRadius, regionPos, regNum, regSize, regW, regH)
            if nN.shape[0]>0:
                tXY.append((x,y))
                mchIdxs.append(nN)
        
        return tXY, mchIdxs
    
    def plotMatch(self, x1, y1, xs1, ys1, x2, y2, xs2, ys2):
        
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
    两组排序的（数值由小到大）特征匹配，当一个特征匹配成功之后，下一个特征的匹配搜索从另一组特征的匹配成功的下一个特征开始检索
    '''  
    def distMatch2(self,oiData, tiData, maxMchDist=1, minMchNum=3):
        
        oiDist = oiData[:,2]
        tiDist = tiData[:,2]
        oIdx = 0
        tIdx = 0
        mchPairs = []
        mchNum = 0
        distError = 0
        while oIdx<len(oiDist):
            oiD = oiDist[oIdx]
            while tIdx<len(tiDist):
                tiD = tiDist[tIdx]
                tdiff = math.fabs(oiD-tiD)
                if tdiff<maxMchDist:
                    mchPairs.append((oiData[oIdx],tiData[tIdx]))
                    mchNum = mchNum +1
                    distError += tdiff
                    tIdx = tIdx+1
                    #oIdx = oIdx+1
                elif oiD<tiD:
                    oIdx = oIdx+1
                    break
                elif oiD>tiD:
                    tIdx = tIdx+1
            if tIdx>=len(tiDist):
                break
        
        meanError = 99
        if mchNum>0:
            meanError = distError/mchNum
            #print("mchNum=%d,meanError=%f"%(mchNum,meanError))
        isMchOk = True
        if mchNum>2:
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
            
        return np.array(mchPairs), isMchOk
                    
    '''
    两组排序的（数值由小到大）特征匹配，每次重新循环，找距离最近的，可能重复匹配
    '''
    def distMatch(self,oiData, tiData, maxMchDist=1, minMchNum=3):
        
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
        if mchNum>2:
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
            
        return np.array(mchPairs), isMchOk
    
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
            
        
    def saveReg(self, pos, fname, radius=4, width=1, color='green'):
        
        with open(fname, 'w') as fp1:
            for tobj in pos:
               fp1.write("image;circle(%.2f,%.2f,%.2f) # color=%s width=%d font=\"times 10\"\n"%
               (tobj[0], tobj[1], radius, color, width))
        
    def posTrans2(self, posMchs, stars):
        
        #print(posMchs)
        for i, tm in enumerate(posMchs):
            if i==0:
                dataOi = posMchs[i][0]
                dataTi = posMchs[i][1]
            else:
                dataOi = np.concatenate([dataOi,posMchs[i][0]])
                dataTi = np.concatenate([dataTi,posMchs[i][1]])
                
        ds9RegionName = "data/oi_ds9.reg" 
        ds9RegionName = "data/ti_ds9.reg"
        #self.saveReg(dataOi, ds9RegionName, radius=4, width=1)
        #self.saveReg(dataTi, ds9RegionName, radius=4, width=1)
               
        print(dataOi.shape)
        #print(dataOi[:3])
        #plt.plot(dataOi[:,0],dataOi[:,1])
        #plt.show()
        #plt.plot(dataTi[:,0],dataTi[:,1])
        #plt.show()
        
        xshift,yshift, xrms, yrms = self.evaluatePos(dataOi, dataTi)
        print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
        
        dataTi2 = dataTi
        dataOi2 = dataOi
        
        h, tmask = cv2.findHomography(dataOi2, dataTi2, cv2.RANSAC, 0.1) #0, RANSAC , LMEDS
        
        dataTi2 = cv2.perspectiveTransform(np.array([dataOi]), h)
        dataTi2 = dataTi2[0]
        
        ds9RegionName = "data/oi2ti_ds9.reg"
        #self.saveReg(dataTi2, ds9RegionName, radius=8, width=2)
        
        xshift,yshift, xrms, yrms = self.evaluatePos(dataTi, dataTi2)
        print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
    
        starPoss = stars[:,3:5]
        starPossTi = cv2.perspectiveTransform(np.array([starPoss]), h)
        starPossTi = starPossTi[0]

        xshift,yshift, xrms, yrms = self.evaluatePos(starPoss, starPossTi)
        stars[:,3:5] = starPossTi
        print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
        
        return stars
    
    def posTrans(self, posMchs, stars):
        
        #print(posMchs)
        for i, tm in enumerate(posMchs):
            if i==0:
                dataOi = posMchs[i][0]
                dataTi = posMchs[i][1]
            else:
                dataOi = np.concatenate([dataOi,posMchs[i][0]])
                dataTi = np.concatenate([dataTi,posMchs[i][1]])
        
        xshift,yshift, xrms, yrms = self.evaluatePos(dataOi, dataTi)
        print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
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
        
        p_init = models.Polynomial2D(degree=1)
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
        print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
    
        starPoss = stars[:,3:5]
        oix = starPoss[:,0]
        oiy = starPoss[:,1]
        tix2 = tixp(oix, oiy)
        tiy2 = tiyp(oix, oiy)
        starPossTi = np.concatenate([tix2.reshape((tix2.shape[0],1)),tiy2.reshape((tix2.shape[0],1))],axis=1)

        xshift,yshift, xrms, yrms = self.evaluatePos(starPoss, starPossTi)
        stars[:,3:5] = starPossTi
        print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
        
        
        return stars
    
    def doAll(self, srcDir, oiFile, tiFile):
                  
        oiData = np.loadtxt("%s/%s"%(srcDir, oiFile))
        tiData = np.loadtxt("%s/%s"%(srcDir, tiFile))
        print("orign")
        print(oiData.shape)
        print(tiData.shape)
        
        oiData = self.filterStar(oiData, xIdx=0, yIdx=1)
        tiData = self.filterStar(tiData, xIdx=0, yIdx=1)
        print("filter")
        print(oiData.shape)
        print(tiData.shape)
        
        brightStarTi, darkStarTi = self.getBright(tiData,100, 11)
        brightStarOi, darkStarOi = self.getBright(oiData, 100, 11)
        print("bright")
        print(brightStarOi.shape)
        print(brightStarTi.shape)
        print("dark")
        print(darkStarOi.shape)
        print(darkStarTi.shape)
        
        ds9RegionName = "data/brightStarTi.reg"
        #self.saveReg(brightStarTi, ds9RegionName, radius=6, width=2, color='red')
        ds9RegionName = "data/brightStarOi.reg"
        #self.saveReg(brightStarOi, ds9RegionName, radius=6, width=2, color='red')
        ds9RegionName = "data/darkStarTi.reg"
        #self.saveReg(darkStarTi, ds9RegionName, radius=4, width=1, color='yellow')
        ds9RegionName = "data/darkStarOi.reg"
        #self.saveReg(darkStarOi, ds9RegionName, radius=4, width=1, color='yellow')
        
        regionPosTi, regionStarNumTi, regNumTi, regSizeTi, regWTi, regHTi = self.createRegionIdx(darkStarTi)
        regionPosOi, regionStarNumOi, regNumOi, regSizeOi, regWOi, regHOi = self.createRegionIdx(darkStarOi)
        
        self.statisticRegions(regionPosTi, regionStarNumTi)
        self.statisticRegions(regionPosOi, regionStarNumOi)
        
        tiXY, mchIdxsTi = self.createMatchIdx(brightStarTi, regionPosTi, regNumTi, regSizeTi, regWTi, regHTi)
        oiXY, mchIdxsOi = self.createMatchIdx(brightStarOi, regionPosOi, regNumOi, regSizeOi, regWOi, regHOi)
        
        if len(tiXY)==0:
            print("%s create feature failure"%(tiFile))
        if len(oiXY)==0:
            print("%s create feature failure"%(oiFile))
        
        tarray = np.array(mchIdxsTi)
        print(tarray.shape)
        tDist = tarray[:,:,2]
        print(tDist.shape)
        tree = KDTree(tDist)
        
        totalMatchNum = 0
        mchList = []
        for i, oIdx in enumerate(mchIdxsOi):
            td = oIdx[:,2]
            mchIdx = tree.query_ball_point(td, 20)
            
            if len(mchIdx)>0:
                for tidx0 in mchIdx:
                    tdata00 = tarray[tidx0]
                    dm, isMchOk = self.distMatch(oIdx, tdata00)
                    if len(dm)>2 and isMchOk:
                        print("query %d match %d******************"%(i, len(mchIdx)))
                        #print(dm)
                        omIdx = dm[:,0]
                        tmIdx = dm[:,1]
                        oxy01 = oiXY[i]
                        ox1 = omIdx[:,0]
                        oy1 = omIdx[:,1]
                        txy02 = tiXY[tidx0]
                        tx2 = tmIdx[:,0]
                        ty2 = tmIdx[:,1]
                        self.plotMatch(oxy01[0],oxy01[1],ox1,oy1,txy02[0],txy02[1],tx2,ty2)
                        totalMatchNum += 1
                        
                        opos = omIdx[:,0:2]
                        tpos = tmIdx[:,0:2]
                        oxy1 = np.concatenate([opos,[oxy01]])
                        txy1 = np.concatenate([tpos,[txy02]])
                        mchList.append((oxy1,txy1))
                        break
                    
        if len(mchList)>1:
            print("totalMatchNum=%d"%(totalMatchNum))
            darkStarOiTi = self.posTrans(mchList, darkStarOi)
            origXY, mchXY = self.match(darkStarOiTi, regionPosTi, regNumTi, regSizeTi, regWTi, regHTi,1)
            
            ds9RegionName = "data/OiMatch.reg"
            #self.saveReg(origXY, ds9RegionName, radius=10, width=2, color='red')
            
            mchXY = np.array(mchXY)
            print(mchXY.shape)
            print(mchXY[:3])
            tdist = mchXY[:,2]
            minD = np.min(tdist)
            maxD = np.max(tdist)
            avgD = np.mean(tdist)
            print("minD=%f,maxD=%f,avgD=%f"%(minD, maxD, avgD))
            print("origNum:%d, after:%d"%(darkStarOiTi.shape[0],mchXY.shape[0]))

def test():
    
    tpath = 'data'
    #tfile1 = 'G031_mon_objt_190116T21430226.cat'
    #tfile2 = 'G041_mon_objt_190101T21551991.cat'
    tfile1 = 'G041_mon_objt_181018T17592546.cat'
    tfile2 = 'G021_mon_objt_181101T17255569.cat'
    
    starMatch = StarMatch()
    starMatch.doAll(tpath, tfile1, tfile2)
    
if __name__ == "__main__":
        
    test()
    