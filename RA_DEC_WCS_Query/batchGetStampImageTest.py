# -*- coding: utf-8 -*-

from astropy.io import fits
import numpy as np
import math
import sys
import os

    
def getWindowImgs(savePath, imgListFileName, size=400):
    
    print("save image to %s"%(savePath))
    if not os.path.exists(savePath):
        os.system("mkdir -p %s"%(savePath))
    
    tcmd = "cp /data/gwac_data/stampImageTest/G231201_C01184/* %s"%(savePath)
    os.system(tcmd)

if __name__ == "__main__":
    
    if len(sys.argv)==3:
        imgListFileName = sys.argv[1]
        #savePath = '/data/gwac_diff_xy/cutfile'
        savePath = sys.argv[2]
        getWindowImgs(savePath, imgListFileName)
    else:
        print("python batchGetStampImageFromQueryResult.py imgListFileName savePath")
        