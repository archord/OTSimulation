# -*- coding: utf-8 -*-

import scipy as S
import numpy as np
import matplotlib.pyplot as plt
from astropy.stats import sigma_clip
from astropy.io import fits
from random import randint

'''
return [(x,y,mag),(),...]
'''
def selectTempOTs(fname, otNum, printFlag=False):
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
    tdata = tdata[(mag>targetMagMin) & (mag<targetMagMax) & (elpct<maxEllipticity) & (fwhm<targetFwhmMax)]
    
    if printFlag:
        print("mag range from %f to %f, select mag from %f to %f"%(minMag, maxMag, targetMagMin, targetMagMax))
        print("with ellipticity less than %f, and fwhm less than %f"%(maxEllipticity, targetFwhmMax))
        print("after filter, left %d objects"%(tdata.shape[0]))
        
        ds9RegionName = fname[:fname.index(".")] + "_ottempsel_ds9.reg"
        with open(ds9RegionName, 'w') as fp1:
            for tobj in tdata:
               fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%ld-%.2f} font=\"times 7\"\n"%
               (tobj[3], tobj[4], 4.0, tobj[0], tobj[38]))
           
    randomIdx = np.random.randint(0, tdata.shape[0], size=otNum)
    ots = []
    for tobj in tdata[randomIdx]:
        ots.append((tobj[3],tobj[4],tobj[38]))
        
    print("selectTempOTs done.")
    maxInstrMag = maxMag
    return ots, maxInstrMag
    
def getPsfTemp(fname,pos,boxs=(10,10),backsky=None):
   """
   select psf template from real image.
   @param fitsf: fits file
   @param pos:  psf template star position
   @param backsky: background sky.
   return star: data of star,
          backsky:bakcground sky
          center:(x,y) of star center with barycenter.
   """
   
   deltx = boxs[0]%2
   delty = boxs[1]%2
   
   xs =  int(pos[0]) - int(boxs[0]/2.)
   xe =  int(pos[0]) + int(boxs[0]/2.) + deltx
   
   ys =  pos[1] - int(boxs[1]/2.)
   ye =  pos[1] + int(boxs[1]/2.) + delty

   data = fits.getdata(fname)
   #print pos,ys,ye,xs,xe
   star=data[ys:ye,xs:xe]
   if not backsky:
      backsky = np.median(np.sort(np.ravel(star))[:int(boxs[0]*boxs[1]/2)])
   print("backsky = %s "%(backsky))

   return star,backsky
   
def addStar(image,psft,posa,flux_ratio=1.):
   """
   @param p: pyfits.open object.
   @param psft: psf template
   @param posa: positon...in [x,y]
   @flux_ratio: to ad star flux ratio to template
   """
   boxs = psft.shape
   delt_x = boxs[0]/2
   delt_y = boxs[1]/2

   xc_as = int( posa[0] - delt_x) 
   xc_ae = int( posa[0] + delt_x ) + boxs[0]%2 

   yc_as = int( posa[1] - delt_y)
   yc_ae = int( posa[1] + delt_y) + boxs[1]%2
    #print "flux_ratio=",flux_ratio
   image[yc_as:yc_ae,xc_as:xc_ae] += psft*flux_ratio

   return image
   
def simulateImageByAddStar1(fname,tempStarPos,tempStarMag=10.,maxmag=16,magbin=0.1,posbin=80,xnum=40,ynum=-1,center=(1000,1000), 
                boxs=[10,10],backsky=None,posamagsfil=None, outfile=None,tag_com=True):
    """
    @20150331,
    add 100 stars in 10x10 columns.with different mags in 1kx1k for miniGWAC
    xnum= columns in x direction. 
    add many stars... with different mag and postion.
    tag_com: true: simulated star+ template. false: only simulated stars in the fits file.
    
    """
    if ynum<0:
       ynum=xnum
    pos = S.int0(tempStarPos)
    star,backsky = getPsfTemp(fname,pos,boxs=boxs,backsky=backsky)
    psft = star
    psft = psft - backsky

    with fits.open(fname) as hdul:
        #hdr0 = hdul[0].header
        data0 = hdul[0].data
        if not tag_com:
           #-- temperate using...
           data0= S.zeros(data0.shape)
           #---
        
        posamags= []
        if posamagsfil == None:
           mags= S.arange(maxmag,maxmag-magbin*xnum,-magbin)
           stx =  int(S.random.randn()*xnum) + center[0]-int(xnum*posbin)
           sty =  int(S.random.randn()*ynum) + center[1]-int(ynum*posbin)
           for i in range(xnum):
               for j in range(ynum):
                    posamags.append([[i*posbin+stx,j*posbin+sty],mags[i]])
        else:
           pmd = S.loadtxt(posamagsfil)
           for pm0 in pmd:
              posamags.append([pm0[:2],pm0[2]])
              
        for posamag in posamags:
            posa,mag_add = posamag
       #     print mag_orig,mag_add
            flux_ratio = 10**((tempStarMag - mag_add)/2.5)
            data0 = addStar(data0,psft,posa,flux_ratio=flux_ratio)
            
        hdul_new = fits.HDUList(hdul)
        #hdul_new.header = hdr0
        #hdul_new.data = data0
        hdul_new.writeto(outfile, overwrite=True)
        hdul_new.close()
        print("output simulated fits file to %s " %(outfile))

        outpre= outfile.split(".")[0]
        regfil= "%s_add_ds9.reg" %outpre
        posfil= "%s_add_pos.cat" %outpre
        fp1= open(regfil,'w')
        fp2= open(posfil,'w')
        for posamag in posamags:
           posa,mag_add = posamag
           fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 7\"\n"%
               (posa[0],posa[1],10.0, mag_add))
           fp2.write("%6.2f %6.2f    %2.1f\n" %(posa[0],posa[1],mag_add))
        fp1.close()
        fp2.close()
     
    print("simulateImageByAddStar1 done.")
    
    return posamags


if __name__ == "__main__":
    
    fitsName = "/home/xy/Downloads/myresource/deep_data2/simot/data/CombZ_0.fit"
    catName = "/home/xy/Downloads/myresource/deep_data2/simot/data/CombZ_0_notMatched.cat"
    simOutFile="/home/xy/Downloads/myresource/deep_data2/simot/data/CombZ_0_simstar1.fit"
    selectNum = 1
    tOTs, maxInstrMag = selectTempOTs(catName,selectNum, printFlag=True)
    print(tOTs)
    tOT1 = tOTs[0]
    tempStarPos1 = [tOT1[0], tOT1[1]]
    tempStarMag1 = 16 - (maxInstrMag - tOT1[2])
    print("Instrument mag is %f, to relative mag is %f"%(tOT1[2], tempStarMag1))
        
    simulateImageByAddStar1(fitsName,tempStarPos1,tempStarMag1,maxmag=16,magbin=0.1,posbin=80,xnum=40,ynum=-1,center=(3700,3700), 
                boxs=[10,10],backsky=None,posamagsfil=None, outfile=simOutFile,tag_com=True)
    
    
