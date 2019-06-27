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
            
    def posTransPolynomial(self, posMchs, stars, order=3):
        
        #print(posMchs)
        for i, tm in enumerate(posMchs):
            if i==0:
                dataOi = posMchs[i][0]
                dataTi = posMchs[i][1]
            else:
                dataOi = np.concatenate([dataOi,posMchs[i][0]])
                dataTi = np.concatenate([dataTi,posMchs[i][1]])
        

        tipos = dataTi.copy()
        tipos[:,0] = tipos[:,0] + 20
        self.saveReg(tipos, "data/tipos%d.reg"%(stars.shape[0]), radius=8, width=1, color='green')
        oipos = dataOi.copy()
        oipos[:,0] = oipos[:,0] + 20
        self.saveReg(oipos, "data/oipos%d.reg"%(stars.shape[0]), radius=8, width=1, color='green')
 
        
        blindStarNum = dataOi.shape[0]
        #xshift,yshift, xrms, yrms = self.evaluatePos(dataOi, dataTi)
        #print("%d blindMatch stars, before trans: xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(dataOi.shape[0], xshift,yshift, xrms, yrms))
          
        #xshift,yshift, xrotation, yrotation = 0, 0, 0, 0
        xshift,yshift, xrotation, yrotation = self.polynomialFitEvulate(dataOi, dataTi)
        #print("fitting: xshift=%.2f, yshift=%.2f, xrotation=%.5f, yrotation=%.5f"%(xshift,yshift, xrotation, yrotation))
        tixp, tiyp = self.polynomialFit(dataOi, dataTi, order)
        
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
    
    def posTransPolynomial2(self, oiMchPos, tiMchPos, stars, order=3):
        
        tixp, tiyp = self.polynomialFit(oiMchPos, tiMchPos, order)
        
        starPoss = stars[:,[self.xIdx, self.yIdx]]
        oix = starPoss[:,0]
        oiy = starPoss[:,1]
        tix2 = tixp(oix, oiy)
        tiy2 = tiyp(oix, oiy)
        starPossTi = np.concatenate([tix2.reshape((tix2.shape[0],1)),tiy2.reshape((tiy2.shape[0],1))],axis=1)
        starTrans = stars.copy()
        starTrans[:,[self.xIdx, self.yIdx]] = starPossTi
        
        return starTrans
    
def doAll(srcDir, oiFile, tiFile):
      
    oiMatch = BlindMatch()
    tiMatch = BlindMatch()
    
    oiData = np.loadtxt("%s/%s"%(srcDir, oiFile))
    tiData = np.loadtxt("%s/%s"%(srcDir, tiFile))
    #print("orign")
    #print(oiData.shape)
    #print(tiData.shape)
    
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
                        
                        '''    
                        ox1 = omIdx[:,0]
                        oy1 = omIdx[:,1]
                        tx2 = tmIdx[:,0]
                        ty2 = tmIdx[:,1]
                        oiMatch.plotBlindMatch(oxy01[0],oxy01[1],ox1,oy1,txy02[0],txy02[1],tx2,ty2)
                        '''
                        break
                
        if len(mchList)>1:
            print("total Match key points %d"%(totalMatchNum))
            starOiTi, xshift,yshift, xrotation, yrotation, blindStarNum = tiMatch.posTransPolynomial(mchList, oiData, 2) # posTransPolynomial posTransPerspective
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
            #print("********** rematch %s use %d micro seconds"%(oiFile, runTime0))
            
            #print(mchPosPairs.shape)
            #print(mchPosPairs[:3])
            mchRatios0, oiPosJoin0,tiPosJoin0, mchData0, xshift0,yshift0, xrms0, yrms0 \
                = crossMatch.evaluateMatchResult(starOiTi, tiData, mchPosPairs)
            #print(mchRatios0)
            
            oiDataMch = oiData[orgPosIdxs]
            #print(oiDataMch.shape)
            #print(oiDataMch[:3])
            
            oiMchPos = oiDataMch[:,0:2]
            tiMchPos = mchPosPairs[:,2:4]
            starOiTiPsp2 = tiMatch.posTransPerspective2(oiMchPos, tiMchPos, oiData)
            starOiTiPly2 = tiMatch.posTransPolynomial2(oiMchPos, tiMchPos, oiData, 3)
            
            starttime = datetime.now()
            mchPosPairs, orgPosIdxs = crossMatch.xyMatch(starOiTiPsp2, 4)
            endtime = datetime.now()
            runTime1 = (endtime - starttime).total_seconds()*1000
            #print("********** rematch %s use %d micro seconds"%(oiFile, runTime1))
            
            #print(mchPosPairs.shape)
            #print(mchPosPairs[:3])
            mchRatios1, oiPosJoin1,tiPosJoin1, mchData1, xshift1,yshift1, xrms1, yrms1 \
                = crossMatch.evaluateMatchResult(starOiTiPsp2, tiData, mchPosPairs)
            #print(mchRatios1)
            
            starttime = datetime.now()
            mchPosPairs, orgPosIdxs = crossMatch.xyMatch(starOiTiPly2, 4)
            endtime = datetime.now()
            runTime2 = (endtime - starttime).total_seconds()*1000
            #print("********** rematch %s use %d micro seconds"%(oiFile, runTime2))
            
            #print(mchPosPairs.shape)
            #print(mchPosPairs[:3])
            mchRatios2, oiPosJoin2,tiPosJoin2, mchData2, xshift2,yshift2, xrms2, yrms2 \
                = crossMatch.evaluateMatchResult(starOiTiPly2, tiData, mchPosPairs)
            #print(mchRatios2)
            
            
            rstStr = "%s %.2f %.2f %.2f %.2f %d %d "\
                "%d %d "\
                "%d %d %d %.2f %.2f %.2f %.2f %.2f %d "\
                "%d %d %d %.2f %.2f %.2f %.2f %.2f %d "\
                "%d %d %d %.2f %.2f %.2f %.2f %.2f %d \n"\
                %(oiFile, xshift,yshift, xrotation, yrotation, blindStarNum, totalMatchNum, \
                  tiData.shape[0], oiData.shape[0], \
                  oiPosJoin0,tiPosJoin0, mchData0, mchRatios0, xshift0,yshift0, xrms0, yrms0,runTime0,\
                  oiPosJoin1,tiPosJoin1, mchData1, mchRatios1, xshift1,yshift1, xrms1, yrms1,runTime1,\
                  oiPosJoin2,tiPosJoin2, mchData2, mchRatios2, xshift2,yshift2, xrms2, yrms2,runTime2)
            #print(rstStr)
            print([mchData0,mchData1,mchData2])
            print([mchRatios0,mchRatios1,mchRatios2])
            print([xshift0,xshift1,xshift2])
            
            ''' '''
            oiDataMch = oiData[orgPosIdxs]
            oiDataNch = np.delete(oiData, orgPosIdxs, axis=0)
            oiMchPos = oiDataMch[:,0:2].copy()
            oiNchPos = oiDataNch[:,0:2].copy()
            oiMchPos[:,0] = oiMchPos[:,0] + 20
            oiNchPos[:,0] = oiNchPos[:,0] + 20
            tiMchPos = mchPosPairs[:,2:4]
            
            crossMatch1 = CrossMatch()
            crossMatch1.createRegionIdx(tiMchPos)
            mchPosPairs, orgPosIdxs = crossMatch1.xyMatch(tiData, 1)

            #print(tiData.shape)
            #print(tiMchPos.shape)
            #print(len(orgPosIdxs))
            tiDataNch = np.delete(tiData, orgPosIdxs, axis=0)
            tiNchPos = tiDataNch[:,0:2].copy()
            tiMchPos[:,0] = tiMchPos[:,0] + 20
            tiNchPos[:,0] = tiNchPos[:,0] + 20
            #print(tiNchPos.shape)
            
            tiMatch.saveReg(oiMchPos, "data/OiMch.reg", radius=4, width=1, color='green')
            tiMatch.saveReg(oiNchPos, "data/OiNch.reg", radius=5, width=1, color='blue')
            tiMatch.saveReg(tiMchPos, "data/TiMch.reg", radius=4, width=1, color='red')
            tiMatch.saveReg(tiNchPos, "data/TiNch.reg", radius=5, width=1, color='yellow')
            
def test():
    
    tpath = 'data'
    #tfile1 = 'G031_mon_objt_190116T21430226.cat'
    #tfile2 = 'G041_mon_objt_190101T21551991.cat'
    oiFile = 'G031_mon_objt_181109T17301855.cat' #G021_mon_objt_181106T17045393.cat G041_mon_objt_181018T17592546
    tiFile = 'G021_mon_objt_181101T17255569.cat'
    
    doAll(tpath, oiFile, tiFile)
    
if __name__ == "__main__":
        
    test()