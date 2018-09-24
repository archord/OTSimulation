# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
from random import random, randint
from astropy.io import fits
import numpy as np
import math
from gwac_util import zscale_image

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
       
       deltx = int(boxs[0]%2)
       delty = int(boxs[1]%2)
       
       xs =  int(pos[0]) - int(boxs[0]/2.)
       xe =  int(pos[0]) + int(boxs[0]/2.) + deltx
       
       ys =  int(pos[1]) - int(boxs[1]/2.)
       ye =  int(pos[1]) + int(boxs[1]/2.) + delty
    
       #print("%f,%f,%f,%f,%f,%f"%(pos[0],pos[1],ys,ye,xs,xe))
       star=imgData[ys:ye,xs:xe]
       if not backsky:
          #backsky = np.median(np.sort(np.ravel(star))[:int(boxs[0]*boxs[1]/2)])
          backsky = np.median(star)
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
            star[star<0] = 0
            flux_ratio = 10**((tobj[2]-10)/2.5)
            star = star*flux_ratio
            otImgs.append(star)
        
        self.otImgs = otImgs
        self.otImgNum = len(otImgs)
        #np.savez_compressed("/run/shm/gwacsim/otImgs.npz", otImgs=otImgs, bkgs=bkgs)
        return otImgs
    
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
    
    '''
    仿真星等占比：
    15.5~16：40%
    14.5~15.5：30%
    13.5~14.5：20%
    12~13.5：10%
    '''
    def randomOTAPos(self, objCat, minMag=12, maxMag=16):
        
        minDis = 8
        maxDis = 12
        
        objOTs = np.loadtxt("%s/%s"%(self.tmpDir, objCat))
        
        #过滤部分亮星
        tmag = objOTs[:, objOTs.shape[1]-2]
        tmaxMag = np.max(tmag)
        objOTs = objOTs[tmag>tmaxMag-3.5]
        
        posA = self.getPos(minDis, maxDis)
        posNum = len(posA)
        
        ots = []
        deltaXY = []
        for tobj in objOTs:
            rmsLevel = random()
            
            if rmsLevel<0.4:
                rmag = maxMag - random()
            elif rmsLevel<0.7:
                rmag = maxMag - 1 - random()
            elif rmsLevel<0.9:
                rmag = maxMag - 2 - random()
            else:
                rmag = maxMag - 3 - random()
            '''    
            if rmsLevel<0.4:
                rmag = maxMag - random() *0.5
            elif rmsLevel<0.7:
                rmag = maxMag - 0.5 - random()
            elif rmsLevel<0.9:
                rmag = maxMag - 1.5 - random()
            else:
                rmag = maxMag - 2.5 - 1.5*random()
            '''    
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
        
        #对同一幅图多次仿真，只用提取一次仿真psf模板
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
                    
                    ctrX = math.ceil(posa[0])
                    ctrY = math.ceil(posa[1])
                    
                    minx = ctrX - 16
                    maxx = ctrX + 16
                    miny = ctrY - 16
                    maxy = ctrY + 16
                    plt.clf()
                    fig, axes = plt.subplots(1, 4, figsize=(6, 8))
                    axes.flat[0].imshow(psft, interpolation = "nearest", cmap='gray')
                    psftz = zscale_image(psft)
                    axes.flat[1].imshow(psftz, interpolation = "nearest", cmap='gray')
                    widImg=data0[miny:maxy,minx:maxx]
                    axes.flat[2].imshow(widImg, interpolation = "nearest", cmap='gray')
                    widImgz = zscale_image(widImg)
                    axes.flat[3].imshow(widImgz, interpolation = "nearest", cmap='gray')
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
    
    