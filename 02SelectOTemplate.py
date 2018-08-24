# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from astropy.stats import sigma_clip

def getOTs(fname):
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
    tdata = np.loadtxt(fname)
    print("total read %d objects"%(tdata.shape[0]))

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
    print("mag range from %f to %f, select mag from %f to %f"%(minMag, maxMag, targetMagMin, targetMagMax))
    print("with ellipticity less than %f, and fwhm less than %f"%(maxEllipticity, targetFwhmMax))
    tdata = tdata[(mag>targetMagMin) & (mag<targetMagMax) & (elpct<maxEllipticity) & (fwhm<targetFwhmMax)]
    print("after filter, left %d objects"%(tdata.shape[0]))
    
    elong = tdata[:,14]
    elpct = tdata[:,15]
    fwhm = tdata[:,18]
    mag = tdata[:,38]
    
    elongIdx = elong<5
    elpctIdx = elpct<0.5
    fwhmIdx = fwhm<5
    elong1 = elong[elongIdx]
    elpct2 = elpct[elpctIdx]
    fwhm3 = fwhm[fwhmIdx]
    mag1 = mag[elongIdx]
    mag2 = mag[elpctIdx]
    mag3 = mag[fwhmIdx]
    
    plt.plot(mag1, elong1, ".")
    plt.title("elong")
    plt.show()
    plt.plot(mag2, elpct2, ".")
    plt.title("elpct")
    plt.show()
    plt.plot(mag3, fwhm3, ".")
    plt.title("fwhm")
    plt.show()
    
if __name__ == "__main__":
    
    fname = "data/test.cat"
    fname2 = "data/CombZ_temp_notMatched.cat"
    getOTs(fname2)