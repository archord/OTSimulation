# -*- coding: utf-8 -*-

from astropy.stats import sigma_clip
import numpy as np
import math
import itertools

def polyfit2d(x, y, z, order=3):
    ncols = (order + 1)**2
    G = np.zeros((x.size, ncols))
    ij = itertools.product(range(order+1), range(order+1))
    for k, (i,j) in enumerate(ij):
        G[:,k] = x**i * y**j
    m, _, _, _ = np.linalg.lstsq(G, z)
    return m

def polyval2d(x, y, m):
    order = int(np.sqrt(len(m))) - 1
    ij = itertools.product(range(order+1), range(order+1))
    z = np.zeros_like(x)
    for a, (i,j) in zip(m, ij):
        z += a * x**i * y**j
    return z

def zscale_image(input_img, contrast=0.25):

    """This emulates ds9's zscale feature. Returns the suggested minimum and
    maximum values to display."""
    
    #samples = input_img.flatten()
    samples = input_img[input_img>0]
    samples = samples[~np.isnan(samples)]
    samples.sort()
    chop_size = int(0.1*len(samples))
    subset = samples[chop_size:-chop_size]
    
    if len(subset)<10:
        return np.array([])

    i_midpoint = int(len(subset)/2)
    I_mid = subset[i_midpoint]

    fit = np.polyfit(np.arange(len(subset)) - i_midpoint, subset, 1)
    # fit = [ slope, intercept]

    z1 = I_mid + fit[0]/contrast * (1-i_midpoint)/1.0
    z2 = I_mid + fit[0]/contrast * (len(subset)-i_midpoint)/1.0
    zmin = z1
    zmax = z2
    
    if zmin<0:
        zmin=0
    if math.fabs(zmin-zmax)<0.000001:
        zmin = np.min(samples)
        zmax = np.max(samples)
    
    zimg = input_img.copy()
    zimg[zimg>zmax] = zmax
    zimg[zimg<zmin] = zmin
    zimg=(((zimg-zmin)/(zmax-zmin))*255).astype(np.uint8)
    
    return zimg


def selectTempOTs(fname, tpath):
#   1 NUMBER                 Running object number                                     
#   2 ALPHA_J2000            Right ascension of barycenter (J2000)                      [deg]
#   3 DELTA_J2000            Declination of barycenter (J2000)                          [deg]
#   4 X_IMAGE                Object position along x                                    [pixel]
#   5 Y_IMAGE                Object position along y                                    [pixel]
#  13 A_IMAGE                Profile RMS along major axis                               [pixel]
#  14 B_IMAGE                Profile RMS along minor axis                               [pixel]
#  15 ELONGATION             A_IMAGE/B_IMAGE                                           
#  16 ELLIPTICITY            1 - B_IMAGE/A_IMAGE                                       
#  17 CLASS_STAR             S/G classifier output                                     
#  18 BACKGROUND             Background at centroid position                            [count]
#  19 FWHM_IMAGE             FWHM assuming a gaussian core                              [pixel]
#  20 FLUX_RADIUS            Fraction-of-light radii                                    [pixel]
#  30 FLAGS                  Extraction flags                                          
#  39 MAG_APER               Fixed aperture magnitude vector                            [mag]
#  40 MAGERR_APER            RMS error vector for fixed aperture mag.                   [mag]
    tdata = np.loadtxt("%s/%s"%(tpath, fname))
    origSize = tdata.shape

    maxEllipticity = 0.1
    mag = tdata[:,38]
    elpct = tdata[:,15]
    fwhm = tdata[:,18]
    
    mag1 = sigma_clip(mag, sigma=2.5, iters=3)
    minMag = np.min(mag1)
    maxMag = np.max(mag1)
    medianFwhm = np.median(fwhm)
    
    targetFwhmMax = medianFwhm
    targetMag = maxMag-6
    targetMagMin = targetMag+1
    targetMagMax = targetMag+3
    tdata = tdata[(mag>targetMagMin) & (mag<targetMagMax) & (elpct<maxEllipticity) & (fwhm<targetFwhmMax)]
    
    ds9RegionName = "%s/%s_filter_ds9.reg"%(tpath, fname[:fname.index(".")])
    with open(ds9RegionName, 'w') as fp1:
        for tobj in tdata:
           fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%ld-%.2f} font=\"times 10\"\n"%
           (tobj[3], tobj[4], 4.0, tobj[0], tobj[38]))
               
    ots = []
    for tobj in tdata:
        ots.append((tobj[3],tobj[4],tobj[38]))        
    
    outCatName = "%ss.cat"%(fname[:fname.index(".")])
    outCatPath = "%s/%s"%(tpath, outCatName)
    with open(outCatPath, 'w') as fp0:
        for tobj in ots:
            tempStarMag1 = 16 - (maxMag - tobj[2])
            fp0.write("%.2f %.2f %.2f\n"%(tobj[0], tobj[1], tempStarMag1))
    
    return outCatName
    
    
def filtByEllipticity(fname, tpath, maxEllip=0.5):
    
    tdata = np.loadtxt("%s/%s"%(tpath, fname))
    elpct = tdata[:,15]
    tdata = tdata[elpct<maxEllip]
    
    ds9RegionName = "%s/%sfe.reg"%(tpath, fname[:fname.index(".")])
    with open(ds9RegionName, 'w') as fp1:
        for tobj in tdata:
           fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%ld-%.2f-%.2f} font=\"times 10\"\n"%
           (tobj[3], tobj[4], 4.0, tobj[0], tobj[38], tobj[15]))
               
    ots = []
    for tobj in tdata:
        ots.append((tobj[3],tobj[4],tobj[38]))     
    
    outCatName = "%sfe.cat"%(fname[:fname.index(".")])
    outCatPath = "%s/%s"%(tpath, outCatName)
    with open(outCatPath, 'w') as fp0:
        for tobj in ots:
            fp0.write("%.2f %.2f %.2f\n"%(tobj[0], tobj[1], tobj[2]))
    
    return outCatName

'''
选择部分假OT，过滤条件：
1）过滤最暗的和最亮的（3%）
2）过滤图像边缘的fSize（200px）
'''
def filtOTs(fname, tpath, darkMagRatio=0.03, brightMagRatio=0.03,fSize=200, imgSize=[4096,4096]):

    tdata = np.loadtxt("%s/%s"%(tpath, fname))
    
    minX = 0 + fSize
    minY = 0 + fSize
    maxX = imgSize[0] - fSize
    maxY = imgSize[1] - fSize

    if tdata.shape[1]==3:
        mag = tdata[:,2]
    else:
        mag = tdata[:,38]
    mag = np.sort(mag)
    maxMag = mag[int((1-darkMagRatio)*tdata.shape[0])]
    minMag = mag[int(brightMagRatio*tdata.shape[0])]
            
    tobjs = []
    for obj in tdata:
        
        if tdata.shape[1]==3:
            tx = obj[0]
            ty = obj[1]
            tmag = obj[2]
        else:
            tx = obj[3]
            ty = obj[4]
            tmag = obj[38]
        if tx>minX and tx <maxX and ty>minY and ty<maxY and tmag<maxMag and tmag>minMag:
            tobjs.append([tx, ty, tmag])
            
    outCatName = "%sf.cat"%(fname[:fname.index(".")])
    outCatPath = "%s/%s"%(tpath, outCatName)
    with open(outCatPath, 'w') as fp0:
        for tobj in tobjs:
           fp0.write("%.2f %.2f %.2f\n"%(tobj[0], tobj[1], tobj[2]))
    
    ds9RegionName = "%s/%s_filter_ds9.reg"%(tpath, fname[:fname.index(".")])
    with open(ds9RegionName, 'w') as fp1:
        for tobj in tobjs:
           fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 10\"\n"%
           (tobj[0], tobj[1], 4.0, tobj[2]))
           
    return outCatName
    
def getDs9Reg(fname, tpath):
    
    tdata = np.loadtxt("%s/%s"%(tpath, fname))
                
    tobjs = []
    for obj in tdata:
        
        if tdata.shape[1]==3:
            tx = obj[0]
            ty = obj[1]
            tmag = obj[2]
        else:
            tx = obj[3]
            ty = obj[4]
            tmag = obj[38]
            
        tobjs.append([tx, ty, tmag])
            
    ds9RegionName = "%s.reg"%(fname[:fname.index(".")])
    ds9RegionPath = "%s/%s"%(tpath, ds9RegionName)
    with open(ds9RegionPath, 'w') as fp1:
        for tobj in tobjs:
           fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 10\"\n"%
           (tobj[0], tobj[1], 4.0, tobj[2]))
           
    return ds9RegionName
    
    
def genFinalOTDs9Reg(tname, tpath, poslist):
    
    objPath = "%s/%s_obj.reg"%(tpath, tname)
    tmpPath = "%s/%s_tmp.reg"%(tpath, tname)
    resiPath = "%s/%s_resi.reg"%(tpath, tname)
    
    ofp= open(objPath,'w')
    tfp= open(tmpPath,'w')
    rfp= open(resiPath,'w')
    
    for tpos in poslist:
        ofp.write("image;circle(%.2f,%.2f,%d) # color=green width=1\n"%(tpos[0], tpos[1], 4))
        tfp.write("image;circle(%.2f,%.2f,%d) # color=green width=1\n"%(tpos[2], tpos[3], 4))
        rfp.write("image;circle(%.2f,%.2f,%d) # color=green width=1\n"%(tpos[4], tpos[5], 4))
        
    rfp.close()
    ofp.close()
    tfp.close()
        
    