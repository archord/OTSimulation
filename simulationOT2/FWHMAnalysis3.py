# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import math
from matplotlib import collections  as mc

def medianFilter(Z, fsize):
    from scipy.signal import medfilt
    Z = medfilt(Z,fsize)
    if fsize==5:
        Z[0][0]=Z[1][1]
        Z[0][1]=Z[1][1]
        Z[1][0]=Z[1][1]
        
        Z[0][-1]=Z[1][-2]
        Z[0][-2]=Z[1][-2]
        Z[-2][0]=Z[1][-2]
        
        Z[-1][-1]=Z[-2][-2]
        Z[-1][-2]=Z[-2][-2]
        Z[-2][-1]=Z[-2][-2]
        
        Z[-1][0]=Z[-2][1]
        Z[-1][1]=Z[-2][1]
        Z[1][-1]=Z[-2][1]
    elif fsize==3:
        Z[0][0]=Z[1][1]
        Z[0][-1]=Z[1][-2]
        Z[-1][-1]=Z[-2][-2]
        Z[-1][0]=Z[-2][1]
    return Z

def genLines(ellp, theta, gridNum, tintervalW, tintervalH):
    
    lines = []
    for i in range(gridNum):
        for j in range(gridNum):
            tlen = ellp[i][j] * 10 * 50
            ttheta = theta[i][j]
            x = int(j*tintervalW + 0.5*tintervalW)
            y = int(i*tintervalH + 0.5*tintervalH)
            deltaX = math.ceil(0.5*tlen*math.cos(ttheta))
            deltaY = math.ceil(0.5*tlen*math.sin(ttheta))
            lines.append([(x+deltaX, y+deltaY), (x-deltaX, y-deltaY)])
            
    return lines
    
def fwhmrGridStatistic(parms, gridNum=40):
    
    catData = np.loadtxt(parms[2])
    imgW = parms[0]
    imgH = parms[1]
    
    tintervalW = imgW/gridNum
    tintervalH = imgH/gridNum
    print("tintervalW=%d"%(tintervalW))
    print("tintervalH=%d"%(tintervalH))
            
    tbuff = []
    tbuff2 = []
    tbuff3 = []
    for i in range(gridNum):
        for j in range(gridNum):
            tbuff.append([])
            tbuff2.append([])
            tbuff3.append([])
    for row in catData:
        tx = row[3]
        ty = row[4]
        xIdx = math.floor(tx/tintervalW)
        yIdx = math.floor(ty/tintervalW)
        if xIdx>= gridNum:
            xIdx = gridNum-1;
        if yIdx>= gridNum:
            yIdx = gridNum-1;
        #print("yIdx=%d,xIdx=%d"%(yIdx, xIdx))
        tIdx = yIdx * gridNum + xIdx
        tbuff[tIdx].append(row[15])  #fwhm: 18  ellipticity: 15 THETA_IMAGE: 40
        tbuff2[tIdx].append(row[18])  #fwhm: 18  ellipticity: 15
        tbuff3[tIdx].append(row[40])
    
    thetaMed = np.zeros((gridNum,gridNum), dtype=float)
    ellpMed = np.zeros((gridNum,gridNum), dtype=float)
    fwhmMed = np.zeros((gridNum,gridNum), dtype=float)
    fwhmMin = np.zeros((gridNum,gridNum), dtype=float)
    fwhmMax = np.zeros((gridNum,gridNum), dtype=float)
    
    x = np.arange(gridNum)
    y = np.arange(gridNum)
    X,Y = np.meshgrid(x,y)
    
    for i in range(gridNum):
        for j in range(gridNum):
            tIdx = i * gridNum + j
            tellp = np.array(tbuff[tIdx])
            tfwhm = np.array(tbuff2[tIdx])
            ttheta= np.array(tbuff3[tIdx])
            if tfwhm.shape[0]==0:
                continue
            tmed = np.median(tellp)
            ellpMed[i][j] = tmed
            
            tmed = np.median(ttheta)
            thetaMed[i][j] = tmed
            
            tmed = np.median(tfwhm)
            tmin = np.min(tfwhm)
            tmax = np.max(tfwhm)
            fwhmMed[i][j] = tmed
            fwhmMin[i][j] = tmin
            fwhmMax[i][j] = tmax
    
    filterSize = 5
    Z1 = medianFilter(ellpMed, filterSize)
    Z2 = medianFilter(fwhmMed, filterSize)
    Z3 = medianFilter(thetaMed, filterSize)
    
    lines = genLines(ellpMed, thetaMed, gridNum, tintervalW, tintervalH)
    ''' '''
    tborder = 5
    if parms[2].find('ffov')>0:
        X = X[tborder:-tborder,tborder:-tborder]
        Y = Y[tborder:-tborder,tborder:-tborder]
        Z1 = Z1[tborder:-tborder,tborder:-tborder]
        Z2 = Z2[tborder:-tborder,tborder:-tborder]
        Z3 = Z3[tborder:-tborder,tborder:-tborder]
    
    X = X * tintervalW
    Y = Y * tintervalH
    
    fig1,ax=plt.subplots(figsize=(16, 4),ncols=3,nrows=1)
    fig1.tight_layout()
    cset = ax[0].contourf(X,Y,Z2,10, cmap=plt.cm.hot_r)  #10颜色分级
    contour = ax[0].contour(X,Y,Z2,8,colors='k')
    ax[0].clabel(contour,fontsize=12,colors='k')
    plt.colorbar(cset, ax=ax[0])
    ax[0].set_title('fwhm')
    ax[0].set_xlabel('image X')
    ax[0].set_ylabel('image Y')
    
    cset = ax[1].contourf(X,Y,Z1,10,cmap=plt.cm.hot_r) 
    contour = ax[1].contour(X,Y,Z1,8,colors='k')
    ax[1].clabel(contour,fontsize=12,colors='k')
    plt.colorbar(cset, ax=ax[1])
    ax[1].set_title('ellipticity')
    ax[1].set_xlabel('image X')
    ax[1].set_ylabel('image Y')    
    
    lc = mc.LineCollection(lines,colors='k', linewidths=1)
    ax[2].add_collection(lc)
    ax[2].autoscale()
    ax[2].margins(0.1)
    ax[2].set_title('line of ellipticity*500 with theta')
    ax[2].set_xlabel('image X')
    ax[2].set_ylabel('image Y')
    plt.show()
    
def test2():
        
    parms1 = [4096,4136, r"E:\fwhm\jfov\oi.cat"]
    parms2 = [4096,4136, r"E:\fwhm\chao\oi.cat"]
    parms3 = [3056,3056, r"E:\fwhm\ffov\oi.cat"]
    parms4 = [3056,3056, r"E:\fwhm\mini-gwac\oi.cat"]
    parms5 = [4096,4136, r"E:\fwhm\G031\oi.cat"]
    parms6 = [4096,4136, r"E:\fwhm\data3\oi.cat"]
    fwhmrGridStatistic(parms6, gridNum=40)
    #fwhmrGridStatistic(parms2, gridNum=40)
    #fwhmrGridStatistic(parms3, gridNum=40)
    #fwhmrGridStatistic(parms4, gridNum=40)
        
def test3():
    
    from matplotlib import collections  as mc
    
    lines = [[(0, 1), (1, 1)], [(2, 3), (3, 3)], [(1, 2), (1, 3)]]
    c = np.array([(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1)])
    
    #lc = mc.LineCollection(lines, colors=c, linewidths=2)
    lc = mc.LineCollection(lines,colors='k', linewidths=1)
    fig, ax = plt.subplots()
    ax.add_collection(lc)
    ax.autoscale()
    ax.margins(0.1)
    plt.show()
            
if __name__ == "__main__":
    
    test2()
    