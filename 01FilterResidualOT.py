# -*- coding: utf-8 -*-

import scipy as S
import numpy as np
import matplotlib.pyplot as plt
from astropy.stats import sigma_clip
from astropy.io import fits
from random import randint
import sys

'''
选择部分假OT，过滤条件：
1）过滤最暗的magRatio（5%）
2）过滤图像边缘的fSize（200px）
'''
def selectFalseOT(fname, magRatio=0.05, fSize=200, imgSize=[4096,4096], printFlag=False):

    tdata = np.loadtxt(fname)
    
    minX = 0 + fSize
    minY = 0 + fSize
    maxX = imgSize[0] - fSize
    maxY = imgSize[1] - fSize

    mag = tdata[:,38]
    mag = np.sort(mag)
    maxMag = mag[int((1-magRatio)*tdata.shape[0])]
    
    tobjs = []
    for obj in tdata:
        tx = obj[3]
        ty = obj[4]
        tmag = tdata[38]
        if tx>minX and tx <maxX and ty>minY and ty<maxY and tmag<maxMag:
            tobjs.append([tx, ty, tmag])
    
    if printFlag:
        print("total read %d objects"%(tdata.shape[0]))
        print("filter maxMag %f"%(maxMag))
        print("after filter, left %d objects"%(len(tobjs)))
        
        ds9RegionName = "%s_filter_ds9.reg"%(fname[:fname.index(".")])
        with open(ds9RegionName, 'w') as fp1:
            for tobj in tobjs:
               fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 12\"\n"%
               (tobj[0], tobj[1], 4.0, tobj[2]))
           
    return tobjs


if __name__ == "__main__":
        
    #fitsName = "/home/xy/Downloads/myresource/deep_data2/simot/data/CombZ_0.fit"
    #catName = "/home/xy/Downloads/myresource/deep_data2/simot/data/CombZ_0_notMatched.cat"
    #simOutFile="/home/xy/Downloads/myresource/deep_data2/simot/data/CombZ_0_simstar1.fit"
    fitsName = sys.argv[1]
    catName= sys.argv[2]
    outpre= fitsName.split(".")[0]
    simOutFile= "%s_simaddstar1.fit" %outpre
    
    selectNum = 1
    tOTs, maxInstrMag = selectTempOTs(catName,selectNum, printFlag=False)
    print(tOTs)
    tOT1 = tOTs[0]
    tempStarPos1 = [tOT1[0], tOT1[1]]
    tempStarMag1 = 16 - (maxInstrMag - tOT1[2])
    print("Instrument mag is %f, to relative mag is %f"%(tOT1[2], tempStarMag1))
        
    simulateImageByAddStar1(fitsName,tempStarPos1,tempStarMag1,maxmag=16,magbin=0.1,posbin=80,xnum=40,ynum=-1,center=(3700,3700), 
                boxs=[10,10],backsky=None,posamagsfil=None, outfile=simOutFile,tag_com=True)
    
    
