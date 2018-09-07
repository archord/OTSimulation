# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
from random import random, randint
from astropy.io import fits
import numpy as np
import math

class ImageSimulation(object):
    
    def __init__(self):
        self.minMag=12
        self.maxMag=16
        self.tmpDir="/run/shm/gwacsim"
        self.otImgs = []
        self.otImgNum = 0

    def getPsfTemp(self, imgData,pos,boxs=(10,10),backsky=None):
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
    
       #data = fits.getdata(fname)
       #print pos,ys,ye,xs,xe
       star=imgData[ys:ye,xs:xe]
       if not backsky:
          backsky = np.median(np.sort(np.ravel(star))[:int(boxs[0]*boxs[1]/2)])
       #print("backsky = %s "%(backsky))
    
       return star,backsky

    #所有的子图像的星等都为10等
    def getTmpOtImgs(self, templateOTFile, templateImage, otNum=100):
        
        tPath = "%s/%s"%(self.tmpDir, templateImage)
        timgData = fits.getdata(tPath)
        
        tmpOTs = np.loadtxt("%s/%s"%(self.tmpDir, templateOTFile))
        tmpOtNum = np.min([tmpOTs.shape[0],otNum])
        randomIdx = np.random.randint(0, tmpOTs.shape[0], size=tmpOtNum)
        otImgs = []
        for tobj in tmpOTs[randomIdx]:
            star,backsky = self.getPsfTemp(timgData,(tobj[0],tobj[1]))
            star = star - backsky
            flux_ratio = 10**((tobj[2]-10)/2.5)
            star = star*flux_ratio
            otImgs.append(star)
        
        self.otImgs = otImgs
        self.otImgNum = len(otImgs)
        #return otImgs
    
    def getPos(self, minDis, maxDis):
        
        tval1 = int(math.sqrt(minDis))
        tval2 = -1* tval1
        
        tpos = []
        for tx in range(-1*maxDis, maxDis, 1):
            if tx>tval2 and tx <tval1:
                continue
            for ty in range(-1*maxDis, maxDis, 1):
                if ty>tval2 and ty <tval1:
                    continue
                tdis = math.sqrt(tx*tx+ty*ty)
                if tdis>minDis and tdis<maxDis:
                    tpos.append((tx,ty))
                    
        return tpos
        
    def randomOTAPos(self, objCat, minMag=12, maxMag=16):
        
        minDis = 5
        maxDis = 12
        
        objOTs = np.loadtxt("%s/%s"%(self.tmpDir, objCat))
        posA = self.getPos(minDis, maxDis)
        posNum = len(posA)
        
        ots = []
        deltaXY = []
        for tobj in objOTs:
            rmag = minMag + math.ceil((maxMag-minMag)*random())
            rposIdx = randint(0, posNum-1)
            rpos = posA[rposIdx]
            deltaXY.append(rpos)
            ots.append((tobj[0]+rpos[0],tobj[1]+rpos[1],rmag))
            
        return ots, deltaXY
    
    
    def addStar(self, image,psft,posa,flux_ratio=1.):
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

    def simulateImage1(self, objCat, objImg, tmpCat, tmpImg, tmpOtNum=100):
        
        if self.otImgNum < tmpOtNum:
            self.getTmpOtImgs(tmpCat, tmpImg, otNum=tmpOtNum)
        
        otAs, deltaXY = self.randomOTAPos(objCat)
        
        destImg = "%s/%s"%(self.tmpDir, objImg)
    
        with fits.open(destImg) as hdul:
            
            tflag = 1
            data0 = hdul[0].data
            for posamag in otAs:
                posa = (posamag[0],posamag[1])
                mag_add = posamag[2]
                rimgIdx = randint(0, self.otImgNum-1)
                psft = self.otImgs[rimgIdx]
                flux_ratio = 10**((10 - mag_add)/2.5)
                data0 = self.addStar(data0,psft,posa,flux_ratio=flux_ratio)
                
                if tflag==0:
                    plt.imshow(psft, cmap='gray')
                    plt.show()
                    
                    ctrX = math.ceil(posa[0])
                    ctrY = math.ceil(posa[1])
                    
                    minx = ctrX - 16
                    maxx = ctrX + 16
                    miny = ctrY - 16
                    maxy = ctrY + 16
                    widImg=data0[miny:maxy,minx:maxx]
                    plt.imshow(widImg, cmap='gray')
                    plt.show()
                    tflag=1
                
            outpre= objImg.split(".")[0]
            regfile= "%s_simaddstar1_ds9.reg" %(outpre)
            posfile= "%s_simaddstar1_pos.cat" %(outpre)
            outfile="%s_simaddstar1.fit" %(outpre)
            
            regPath = "%s/%s"%(self.tmpDir, regfile)
            posPath = "%s/%s"%(self.tmpDir, posfile)
            outPath = "%s/%s"%(self.tmpDir, outfile)
            
            hdul_new = fits.HDUList(hdul)
            hdul_new.writeto(outPath, overwrite=True)
            hdul_new.close()
            print("output simulated fits file to %s " %(outfile))
    
            fp1= open(regPath,'w')
            fp2= open(posPath,'w')
            for posamag in otAs:
                posa = (posamag[0],posamag[1])
                mag_add = posamag[2]
                fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 7\"\n"%
                   (posa[0],posa[1],10.0, mag_add))
                fp2.write("%6.2f %6.2f %2.1f\n" %(posa[0],posa[1],mag_add))
            fp1.close()
            fp2.close()
         
        print("simulateImageByAddStar1 done.")
        
        return outfile, posfile, deltaXY

    #仿真图像，用于残差图和观测图像对齐时拟合用
    def simulateImage2(self, objImg, tmpCat, tmpImg, tmpOtNum=1, tempStarMag=10.,
                       maxmag=16,magbin=0.1,posbin=80,xnum=40,ynum=40,center=(3700,3700)):
        
        if self.otImgNum == 0:
            self.getTmpOtImgs(tmpCat, tmpImg, otNum=tmpOtNum)
        
        destImg = "%s/%s"%(self.tmpDir, objImg)
    
        with fits.open(destImg) as hdul:
            
            posamags= []
            tmag = 10
            stx =  int(np.random.randn()*xnum) + center[0]-int(xnum*posbin)
            sty =  int(np.random.randn()*ynum) + center[1]-int(ynum*posbin)
            for i in range(xnum):
                for j in range(ynum):
                     posamags.append([i*posbin+stx,j*posbin+sty,tmag])
            
            psft = self.otImgs[0]
            data0 = hdul[0].data
            for posamag in posamags:
                posa = (posamag[0],posamag[1])
                mag_add = posamag[2]
                flux_ratio = 10**((10 - mag_add)/2.5)
                data0 = self.addStar(data0,psft,posa,flux_ratio=flux_ratio)
                                
            outpre= objImg.split(".")[0]
            regfile= "%s_sim4calib_ds9.reg" %(outpre)
            posfile= "%s_sim4calib_pos.cat" %(outpre)
            outfile="%s_sim4calib.fit" %(outpre)
            
            regPath = "%s/%s"%(self.tmpDir, regfile)
            posPath = "%s/%s"%(self.tmpDir, posfile)
            outPath = "%s/%s"%(self.tmpDir, outfile)
            
            hdul_new = fits.HDUList(hdul)
            hdul_new.writeto(outPath, overwrite=True)
            hdul_new.close()
            print("output simulated fits file to %s " %(outfile))
    
            fp1= open(regPath,'w')
            fp2= open(posPath,'w')
            for posamag in posamags:
                posa = (posamag[0],posamag[1])
                mag_add = posamag[2]
                fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 7\"\n"%
                   (posa[0],posa[1],10.0, mag_add))
                fp2.write("%6.2f %6.2f %2.1f\n" %(posa[0],posa[1],mag_add))
            fp1.close()
            fp2.close()
         
        print("simulateImageByAddStar1 done.")
        
        return outfile, posfile
    
    
    def simulateImage3(self, objCat, objImg, tmpCat, tmpImg, simObjNum, tmpOtNum=100):
        
        if self.otImgNum < tmpOtNum:
            self.getTmpOtImgs(tmpCat, tmpImg, otNum=tmpOtNum)
        
        otAs = []
        deltaXY = []
        tnum = 0
        while tnum<simObjNum*2:
            tot, tdlt = self.randomOTAPos(objCat)
            
            tnum = tnum + len(tot)
            otAs.extend(tot)
            deltaXY.extend(tdlt)
            
            print("total %d, now %d"%(simObjNum, tnum))
        
        destImg = "%s/%s"%(self.tmpDir, objImg)
    
        with fits.open(destImg) as hdul:
            
            data0 = hdul[0].data
            for posamag in otAs:
                posa = (posamag[0],posamag[1])
                mag_add = posamag[2]
                rimgIdx = randint(0, self.otImgNum-1)
                psft = self.otImgs[rimgIdx]
                flux_ratio = 10**((10 - mag_add)/2.5)
                data0 = self.addStar(data0,psft,posa,flux_ratio=flux_ratio)
                
                
            outpre= objImg.split(".")[0]
            regfile= "%s_simaddstar1_ds9.reg" %(outpre)
            posfile= "%s_simaddstar1_pos.cat" %(outpre)
            outfile="%s_simaddstar1.fit" %(outpre)
            
            regPath = "%s/%s"%(self.tmpDir, regfile)
            posPath = "%s/%s"%(self.tmpDir, posfile)
            outPath = "%s/%s"%(self.tmpDir, outfile)
            
            hdul_new = fits.HDUList(hdul)
            hdul_new.writeto(outPath, overwrite=True)
            hdul_new.close()
            print("output simulated fits file to %s " %(outfile))
    
            fp1= open(regPath,'w')
            fp2= open(posPath,'w')
            for posamag in otAs:
                posa = (posamag[0],posamag[1])
                mag_add = posamag[2]
                fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 7\"\n"%
                   (posa[0],posa[1],10.0, mag_add))
                fp2.write("%6.2f %6.2f %2.1f\n" %(posa[0],posa[1],mag_add))
            fp1.close()
            fp2.close()
         
        print("simulateImageByAddStar1 done.")
        
        return outfile, posfile, deltaXY
    
    