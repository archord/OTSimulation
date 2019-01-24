# -*- coding: utf-8 -*-
from astropy.io import fits
import numpy as np
import math
import os
import shutil
from datetime import datetime
import matplotlib.pyplot as plt
from DataPreprocess import getData, getData2, getRealData, saveImgs
from gwac_util import zscale_image

def doAll():
    
    fotpath = "/home/xy/Downloads/myresource/deep_data2/simot/multi_scale_20190120/all"
    totpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_20190120"
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/simot/multi_scale_20190120/20190116tot"
    
    #dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    dateStr = '20190122'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    tSampleNamePart = "64_fot10w_%s"%(dateStr)
    
    X,Y,s2n = getData2(totpath, fotpath, workPath, tSampleNamePart)
    #X,Y,s2n = getRealData(realDataPath, workPath, tSampleNamePart)
    

    magerr = s2n[Y[:,1]==1]
    magerr2 = s2n[Y[:,1]==0]
    print(s2n.shape[0])
    print(magerr.shape[0])
    print(magerr2.shape[0])

    from matplotlib.ticker import MultipleLocator, FormatStrFormatter
    xmajorLocator   = MultipleLocator(10)
    xminorLocator   = MultipleLocator(5)

    plt.figure(figsize = (6, 3))
    ax = plt.subplot(111)
    plt.hist(magerr, bins=20, range=(0,100), normed=False,     
            weights=None, cumulative=False, bottom=None,     
            histtype=u'bar', align=u'left', orientation=u'vertical',     
            rwidth=0.6, log=False, color='lightgreen', label=None, stacked=False,     
            hold=None) 
    ax.xaxis.set_major_locator(xmajorLocator)
    ax.xaxis.set_minor_locator(xminorLocator)
    ax.set_xlim(0, 100)
    ax.set_ylabel("number of star")
    ax.set_xlabel('s2n of star')
    plt.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)
    #plt.grid()
    #plt.show()
    plt.savefig('s2nAll.png')
    
    xmajorLocator   = MultipleLocator(1)
    plt.figure(figsize = (5, 3))
    ax = plt.subplot(111)
    plt.hist(magerr, bins=20, range=(0,20), normed=False,     
            weights=None, cumulative=False, bottom=None,     
            histtype=u'bar', align=u'left', orientation=u'vertical',     
            rwidth=0.6, log=False, color='darkorange', label=None, stacked=False,     
            hold=None) 
    ax.xaxis.set_major_locator(xmajorLocator)
    ax.set_xlim(4, 20)
    #plt.grid()
    #plt.show()
    plt.savefig('s2nPart.png')
    
def doAll2():
    
    fotpath = "/home/xy/Downloads/myresource/deep_data2/simot/ot2_img_collection_20190110"
    #totpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0929"
    totpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_1227"
    
    #dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    dateStr = '20190111'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    X,Y,s2n = getData(totpath, fotpath, workPath)
    magerr = s2n[Y[:,1]==1]

    from matplotlib.ticker import MultipleLocator, FormatStrFormatter
    xmajorLocator   = MultipleLocator(5)
    xminorLocator   = MultipleLocator(2)

    plt.figure(figsize = (6, 4))
    ax = plt.subplot(111)
    plt.hist(magerr, bins=20, range=(0,100), normed=False,     
            weights=None, cumulative=False, bottom=None,     
            histtype=u'bar', align=u'left', orientation=u'vertical',     
            rwidth=0.6, log=False, color='lightgreen', label=None, stacked=False,     
            hold=None) 
    ax.xaxis.set_major_locator(xmajorLocator)
    ax.xaxis.set_minor_locator(xminorLocator)
    ax.set_xlim(0, 100)
    ax.set_ylabel("number of star")
    ax.set_xlabel('s2n of star')
    plt.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)
    #plt.grid()
    #plt.show()
    plt.savefig('s2nAll8.png')
    
    xmajorLocator   = MultipleLocator(1)
    plt.figure(figsize = (4, 3))
    ax = plt.subplot(111)
    plt.hist(magerr, bins=20, range=(0,20), normed=False,     
            weights=None, cumulative=False, bottom=None,     
            histtype=u'bar', align=u'left', orientation=u'vertical',     
            rwidth=0.6, log=False, color='darkorange', label=None, stacked=False,     
            hold=None) 
    ax.xaxis.set_major_locator(xmajorLocator)
    ax.set_xlim(4, 20)
    #plt.grid()
    #plt.show()
    plt.savefig('s2nPart8.png')
    
if __name__ == "__main__":
    
    doAll()



