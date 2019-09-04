# -*- coding: utf-8 -*-
from astropy.io import fits
import numpy as np
import math
import os
import traceback
import subprocess
import scipy as S
import DESTPreprocessing as destp
import DESTFeatureExtract as destfe


def sextractor(tpath, fitName):
    
    preName = fitName.split('.')[0]
    catName = "%s.cat"%(preName)
    catPath = "%s/%s"%(tpath, catName)
    fitPath = "%s/%s"%(tpath, fitName)
    
    sexRoot = '/home/xy/Downloads/myresource/deep_data2/image_diff/tools/simulate_tools/config/'
    sexCfg = '%s/OTsearch.sex'%(sexRoot)
    sexParm = '%s/OTsearch.par'%(sexRoot)
    tcmd = 'sex %s -c %s -PARAMETERS_NAME %s -CATALOG_NAME %s -DETECT_MINAREA 3 -DETECT_THRESH 2.5 -ANALYSIS_THRESH 2.5'%(fitPath, sexCfg, sexParm, catPath)
    
    os.system(tcmd)
    

def getCats():
    
    srcPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190812/fit2'
    tdirs = os.listdir(srcPath)
    for tdir in tdirs:
        srcPath1 = "%s/%s"%(srcPath,tdir)
        tfiles = os.listdir(srcPath1)
        for i, tfile in enumerate(tfiles):
            if tfile[-7:]=='rsi.fit':
                try:
                    if i%300==1:
                        print(i)
                    sextractor(srcPath1, tfile)
                except Exception as e:
                    print(e)
                    tstr = traceback.format_exc()
                    print(tstr)

def getCenterOTParms(tpath, width=64, height=64, radius=5):
    
    ctrX = width/2
    ctrY = width/2
    tdata = np.loadtxt(tpath)
    #print(tdata.shape)
    X = tdata[:,3]
    Y = tdata[:,4]
    
    index = (X>ctrX-radius) & (X<ctrX+radius) & (Y>ctrY-radius) & (Y<ctrY+radius)
    tdata0 = tdata[index]
    #print(tdata0)
    if tdata0.shape[0]>1:
        tflux = tdata0[:,5]
        otParm = tdata0[np.argmax(tflux)]
    elif tdata0.shape[0]==1:
        otParm = tdata0
    else:
        otParm = np.array([])
    
    if len(otParm.shape)>1:
        otParm = otParm[0]
        
    return otParm

def getWindowImg(img, ctrPos, size):
    
    imgSize = img.shape
    hsize = int(size/2)
    tpad = int(size%2)
    ctrX = math.ceil(ctrPos[0])
    ctrY = math.ceil(ctrPos[1])
    
    minx = int(ctrX - hsize)
    maxx = int(ctrX + hsize + tpad)
    miny = int(ctrY - hsize)
    maxy = int(ctrY + hsize + tpad)
    
    widImg = []
    if minx>0 and miny>0 and maxx<imgSize[1] and maxy<imgSize[0]:
        widImg=img[miny:maxy,minx:maxx]
        
    return widImg

def prepareFeature(tparm, tdata, width=64, height=64, stampWidth=31):
    
    #ctrX = tdata.shape[1]/2
    #ctrY = tdata.shape[0]/2
    ctrX = tparm[3]
    ctrY = tparm[4]
    c = tparm

    # difference images
    Flux_d = getWindowImg(tdata, (ctrX, ctrY), stampWidth)
    # Compress cutout by calling function compress
    CFlux_d = destp.compressFluxValue(Flux_d)
    # method 1 : Rescale cutout by calling function rescaleFluxValue
    RFlux_d = destp.rescaleFluxValue(CFlux_d)
    if len(RFlux_d) == 1 and 999999999 in RFlux_d:
        return []
    # method 2 : Rescale cutout by calling function bRescaleFluxValue
    BRFlux_d = destp.bRescaleFluxValue(Flux_d)
    # Feature libraries
    # f_aper
    f_aper = c[5]
    # n2sig5; n3sig5; n2sig3; n3sig3
    n2sig5 = destfe.nsig(RFlux_d,2,5)
    n3sig5 = destfe.nsig(RFlux_d,3,5)
    n2sig3 = destfe.nsig(RFlux_d,2,3)
    n3sig3 = destfe.nsig(RFlux_d,3,3)
    # colmeds
    colmeds = destfe.colmeds(BRFlux_d)
    # ellipticity
    ellipticity = c[15]
    # diffsum
    diffsum = destfe.diffsum(RFlux_d)
    # numneg
    numneg = destfe.numneg(RFlux_d)
    # flags
    flags = c[29]
    # class-star
    class_star = c[16]
    # mag_aper
    mag_aper = c[38]
    # magerr_aper
    magerr_aper = c[39]
    # r_AperISO
    r_AperISO = f_aper*1.0/c[7]
    # r_AperISOC
    r_AperISOC = f_aper*1.0/c[9]
    # r_maxtot
    r_maxtot = c[11]*1.0/f_aper
    # Flux_Radius1
    Flux_Radius1 = c[20]
    # Flux_Radius2
    Flux_Radius2 = c[26]
    # A_IMAGE
    A_IMAGE = c[12]
    # B_IMAGE
    B_IMAGE = c[13]
    # ISO0
    ISO0 = c[30]
    # ISO1
    ISO1 = c[31]
    # ISO2
    ISO2 = c[32]
    # ISO3
    ISO3 = c[33]
    # ISO4
    ISO4 = c[34]
    feature = [f_aper,n2sig5,n3sig5,n2sig3,n3sig3,colmeds,ellipticity,diffsum,numneg,
               flags,class_star,mag_aper,magerr_aper,r_AperISO,r_AperISOC,r_maxtot,
               Flux_Radius1,Flux_Radius2,A_IMAGE,B_IMAGE,ISO0,ISO1,ISO2,ISO3,ISO4]

    return feature

def getFeature(tpath, fitName):
    
    preName = fitName.split('.')[0]
    catName = "%s.cat"%(preName)
    catPath = "%s/%s"%(tpath, catName)
    fitPath = "%s/%s"%(tpath, fitName)
    
    otParm = getCenterOTParms(catPath)
    if otParm.shape[0]>0:
        otImg = fits.getdata(fitPath)
        otFeature = prepareFeature(otParm, otImg)
    else:
        otFeature=[]
    return otFeature

def getFeatures():
        
    srcPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190812/fit2'
    tdirs = os.listdir(srcPath)
    
    features = []
    labels = []
    fnames = []
    for tdir in tdirs:
        srcPath1 = "%s/%s"%(srcPath,tdir)
        tfiles = os.listdir(srcPath1)
        for i, tfile in enumerate(tfiles):
            if tfile[-7:]=='rsi.fit':
                try:
                    if i%300==1:
                        print(i)
                    otFeature = getFeature(srcPath1, tfile)
                    if len(otFeature)>0:
                        features.append(otFeature)
                        labels.append(tdir)
                        fnames.append(tfile)
                    else:
                        print("%d, %s has no feature"%(i, tfile))
                except Exception as e:
                    print(e)
                    tstr = traceback.format_exc()
                    print(tstr)
    
    np.savez_compressed("%s/features2.npz"%(srcPath), features=features, labels=labels, fnames=fnames)
    
def test():
    
    srcPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190812/fit/0'
    fitName = 't0000272rsi.fit'
    otFeature=getFeature(srcPath, fitName)
    print(otFeature)
    
if __name__ == "__main__":
    
    getCats()
    #getFeatures()
    #test()

