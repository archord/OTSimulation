# -*- coding: utf-8 -*-
import numpy as np
import os
import math
import cv2
from astrotools import AstroTools


def evaluatePos(srcDir, oiFile, tiFile, mchPair, isAbs=False):
              
    tdata1 = np.loadtxt("%s/%s"%(srcDir, oiFile))
    tdata2 = np.loadtxt("%s/%s"%(srcDir, tiFile))
    tIdx1 = np.loadtxt("%s/%s"%(srcDir, mchPair)).astype(np.int)
    
    tMin = np.min([tdata1.shape[0], tdata2.shape[0]])
    percentage = tIdx1.shape[0]*1.0/tMin
    
    print("getMatchPosHmg: osn16:%d tsn16:%d osn16_tsn16_cm5:%d, pect:%.3f"%(tdata1.shape[0], tdata2.shape[0],tIdx1.shape[0],percentage))
    
    tIdx1 = tIdx1 - 1
    pos1 = tdata1[tIdx1[:,0]][:,0:2]
    pos2 = tdata2[tIdx1[:,1]][:,0:2]
    
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
    print("xshift=%.2f, yshift=%.2f, xrms=%.5f, yrms=%.5f"%(xshift,yshift, xrms, yrms))
    
def posReg(tools, tfile, ofile):
    
    data1 = np.loadtxt(tfile)
    data2 = np.loadtxt(ofile)
    
    dataTi = data1[:,3:5]
    dataOi = data2[:,3:5]
    #print(dataTi[:3])
    #print(dataOi[:3])
    
    minLen = dataTi.shape[0]
    if minLen>dataOi.shape[0]:
        minLen=dataOi.shape[0]
    
    dataTi2 = dataTi[:minLen]
    dataOi2 = dataOi[:minLen]
        
    h, tmask = cv2.findHomography(dataOi2, dataTi2, cv2.RANSAC, 0.1) #0, RANSAC , LMEDS
    
    dataTi2 = cv2.perspectiveTransform(np.array([dataOi]), h)
    dataTi2 = dataTi2[0]
    data2[:,3:5] = dataTi2
    
    saveName = "%s_trans.cat"%(ofile.split(".")[0])
    np.savetxt(saveName, data2, fmt='%.4f')
    
    ofile = saveName
    tmpDir = "/dev/shm/gwacsim/opencvTest"
    os.system("rm -rf %s"%(tmpDir))
    if not os.path.exists(tmpDir):
        os.system("mkdir -p %s"%(tmpDir))
    os.system("cp %s %s/%s"%(tfile, tmpDir, tfile))
    os.system("cp %s %s/%s"%(ofile, tmpDir, ofile))
    mchFile, nmhFile, mchPair = tools.runCrossMatch(tmpDir, tfile, ofile, 1)
    evaluatePos(tmpDir, tfile, ofile, mchPair)
    
def test():
    
    toolPath = '/home/xy/Downloads/myresource/deep_data2/image_diff' #os.getcwd()
    tools = AstroTools(toolPath)
    
    file1 = 'G034_mon_objt_190211T12192603.cat'
    file2 = 'G034_mon_objt_190227T12304321.cat'
    file3 = 'G034_mon_objt_190324T12222033.cat'
    file4 = 'G044_mon_objt_190305T13070793.cat'
    
    posReg(tools, file1, file2)
    posReg(tools, file1, file3)
    posReg(tools, file1, file4)
    
if __name__ == "__main__":
        
    test()
    