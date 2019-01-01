# -*- coding: utf-8 -*-
import numpy as np
import os
import math
import subprocess
import datetime
import cv2
from astropy.io import fits
import warnings
import requests
from astropy.modeling import models, fitting


class AstroTools(object):
    
    def __init__(self, rootPath, log): 
        
        self.varDir = "%s/tools/simulate_tools"%(rootPath)
        self.matchProgram="%s/tools/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"%(rootPath)
        self.imgDiffProgram="%s/tools/hotpants/hotpants"%(rootPath)
        self.funpackProgram="%s/tools/cfitsio/funpack"%(rootPath)
    
        os.environ['VER_DIR'] = self.varDir
        self.log = log
        
    #catalog self match
    def runSelfMatch(self, srcDir, fname, mchRadius):
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(srcDir, fname)
        
        # run sextractor from the unix command line
        cmd = [self.matchProgram, fullPath, str(mchRadius), '1', '2', '12']
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        #self.log.debug(stdoutstr)
        #self.log.debug(stderrstr)
        
        mchFile = "%s_sm%d.cat"%(outpre,mchRadius)
        nmhFile = "%s_sn%d.cat"%(outpre,mchRadius)
        mchFilePath = "%s/%s"%(srcDir,mchFile)
        nmhFilePath = "%s/%s"%(srcDir,nmhFile)
        if os.path.exists(mchFilePath) and os.path.exists(nmhFilePath) and status==0:
            self.log.debug("run self match success.")
            self.log.debug("generate matched file %s"%(mchFile))
            self.log.debug("generate not matched file %s"%(nmhFile))
        else:
            self.log.error("self match failed.")
        
        return mchFile, nmhFile
    
    #crossmatch 
    def runCrossMatch(self, srcDir, objCat, tmpCat, mchRadius):
        
        objpre= objCat.split(".")[0]
        tmppre= tmpCat.split(".")[0]
        objFPath = "%s/%s"%(srcDir, objCat)
        tmpFPath = "%s/%s"%(srcDir, tmpCat)
        outFPath = "%s/%s_%s.out"%(srcDir, objpre,tmppre)
        
        # run sextractor from the unix command line
        cmd = [self.matchProgram, tmpFPath, objFPath, outFPath, str(mchRadius), '1', '2', '12']
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        #self.log.info(stdoutstr)
        #self.log.info(stderrstr)
        
        mchPair = "%s_%s_cm%d.pair"%(objpre,tmppre,mchRadius)
        mchFile = "%s_%s_cm%d.cat"%(objpre,tmppre,mchRadius)
        nmhFile = "%s_%s_cn%d.cat"%(objpre,tmppre,mchRadius)
        mchPairPath = "%s/%s"%(srcDir,mchPair)
        mchFilePath = "%s/%s"%(srcDir,mchFile)
        nmhFilePath = "%s/%s"%(srcDir,nmhFile)
        if os.path.exists(mchPairPath) and os.path.exists(mchFilePath) and os.path.exists(nmhFilePath) and status==0:
            self.log.debug("run catalog match success.")
            self.log.debug("generate pair file %s"%(mchPair))
            self.log.debug("generate matched file %s"%(mchFile))
            self.log.debug("generate not matched file %s"%(nmhFile))
        else:
            self.log.error("cross match failed.")
        
        return mchFile, nmhFile, mchPair
    

    def run_wcs(self, image_in, image_out, ra, dec, width=4096, height=4136):
    
        self.log.info('Executing run_wcs ...')
        
        astronet_tweak_order = 3
        scale_low = 0.98
        scale_high = 1.02
        base='abcd'
        astronet_radius = 1.5
    
        #scampcat = image_in.replace('.fits','.scamp')
        cmd = ['solve-field', '--no-plots', #'--no-fits2fits', cloud version of astrometry does not have this arg
               '--x-column', 'XWIN_IMAGE', '--y-column', 'YWIN_IMAGE',
               '--sort-column', 'FLUX_AUTO',
               '--no-remove-lines', '--uniformize', '0',
               # only work on brightest sources
               #'--objs', '1000',
               '--width', str(width), '--height', str(height),           
               #'--keep-xylist', sexcat,
               # ignore existing WCS headers in FITS input images
               #'--no-verify', 
               #'--verbose',
               #'--verbose',
               #'--parity', 'neg',
               #'--code-tolerance', str(0.01), 
               #'--quad-size-min', str(0.1),
               # for KMTNet images restrict the max quad size:
               #'--quad-size-max', str(0.1),
               # number of field objects to look at:
               '--depth', '50,150,200,250,300,350,400,450,500',
               #'--scamp', scampcat,
               image_in,
               '--tweak-order', str(astronet_tweak_order), '--scale-low', str(scale_low),
               '--scale-high', str(scale_high), '--scale-units', 'app',
               '--ra', str(ra), '--dec', str(dec), '--radius', str(astronet_radius),
               '--new-fits', image_out, '--overwrite',
               '--out', base
        ]
        
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.info(stdoutstr)
        self.log.info(stderrstr)
    
        return

    def ldac2fits (self, cat_ldac, cat_fits):

        '''
        This function converts the LDAC binary FITS table from SExtractor
            to a common binary FITS table (that can be read by Astrometry.net) 
        '''
    
        # read input table and write out primary header and 2nd extension
        with fits.open(cat_ldac) as hdulist:
            hdulist_new = fits.HDUList([hdulist[0], hdulist[2]])
            hdulist_new.writeto(cat_fits, overwrite=True)
            hdulist_new.close()


    #source extract
    def runSextractor(self, fname, srcPath, dstPath, fpar='OTsearch.par', 
                      sexConf=['-DETECT_MINAREA','5','-DETECT_THRESH','3','-ANALYSIS_THRESH','3'], 
                      fconf='OTsearch.sex',
                      cmdStatus=1):
        
        starttime = datetime.datetime.now()
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(srcPath, fname)
        cnfPath = "%s/config/%s"%(self.varDir, fconf)
        outParmPath = "%s/config/%s"%(self.varDir, fpar) #sex_diff.par  OTsearch.par  sex_diff_fot.par
        
        outFile = "%s.cat"%(outpre)
        outFPath = "%s/%s"%(dstPath, outFile)
        outCheckPath = "%s/%s_bkg.fit"%(dstPath, outpre)
        
        #DETECT_MINAREA   5              # minimum number of pixels above threshold
        #DETECT_THRESH    3.0             #  <sigmas>  or  <threshold>,<ZP>  in  mag.arcsec-2  
        #ANALYSIS_THRESH  3.0
        # run sextractor from the unix command line
        if cmdStatus==0:
            cmd = ['sex', fullPath, '-c', cnfPath, '-CATALOG_NAME', outFPath, '-PARAMETERS_NAME', outParmPath,
                   '-CHECKIMAGE_TYPE', 'BACKGROUND', '-CHECKIMAGE_NAME', outCheckPath]
        else:
            cmd = ['sex', fullPath, '-c', cnfPath, '-CATALOG_NAME', outFPath, '-PARAMETERS_NAME', outParmPath]
            
        cmd = cmd + sexConf
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        #self.log.info(stdoutstr)
        #self.log.info(stderrstr)
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run sextractor success.")
            self.log.debug("generate catalog %s"%(outFPath))
        else:
            self.log.debug("sextractor failed.")
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("run sextractor use %d seconds"%(runTime))
            
        return outFile
    
        #hotpants
    def runHotpants(self, objImg, tmpImg, srcDir):
        
        starttime = datetime.datetime.now()
        
        objpre= objImg.split(".")[0]
        tmppre= tmpImg.split(".")[0]
        objFPath = "%s/%s"%(srcDir, objImg)
        tmpFPath = "%s/%s"%(srcDir, tmpImg)
        outFile = "%s_%s_resi.fit"%(objpre,tmppre)
        outFPath = "%s/%s"%(srcDir, outFile)
        
        # run sextractor from the unix command line
        #/home/xy/program/C/hotpants/hotpants -inim oi.fit -tmplim ti.fit -outim oi_ti_resi.fit -v 0 -nrx 4 -nry 4
        cmd = [self.imgDiffProgram, '-inim', objFPath, '-tmplim', tmpFPath, '-outim', 
                 outFPath, '-v', '0', '-nrx', '4', '-nry', '4', '-nsx', '6', '-nsy', '6', '-r', '6']
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        #self.log.info(stdoutstr)
        #self.log.info(stderrstr)
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run hotpants success.")
            self.log.debug("generate diff residual image %s"%(outFPath))
        else:
            self.log.error("hotpants failed.")
            
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("run hotpants use %d seconds"%(runTime))
            
        return outFile
    
    def getWindowImg(self, img, ctrPos, size):
        
        imgSize = img.shape
        hsize = int(size/2)
        tpad = int(size%2)
        ctrX = math.ceil(ctrPos[0])
        ctrY = math.ceil(ctrPos[1])
        
        minx = ctrX - hsize
        maxx = ctrX + hsize + tpad
        miny = ctrY - hsize
        maxy = ctrY + hsize + tpad
        
        widImg = []
        if minx>0 and miny>0 and maxx<imgSize[1] and maxy<imgSize[0]:
            widImg=img[miny:maxy,minx:maxx]
            
        return widImg
    
    def getWindowImgs(self, srcDir, objImg, tmpImg, resiImg, datalist, size):
        
        objPath = "%s/%s"%(srcDir, objImg)
        tmpPath = "%s/%s"%(srcDir, tmpImg)
        resiPath = "%s/%s"%(srcDir, resiImg)
        
        objData = fits.getdata(objPath)
        tmpData = fits.getdata(tmpPath)
        resiData = fits.getdata(resiPath)
        
        subImgs = []
        parms = []
        for td in datalist:
            objWid = self.getWindowImg(objData, (td[0], td[1]), size)
            tmpWid = self.getWindowImg(tmpData, (td[0], td[1]), size)
            resiWid = self.getWindowImg(resiData, (td[0], td[1]), size)
            
            if len(objWid)>0 and len(tmpWid)>0 and len(resiWid)>0:
                subImgs.append([objWid, tmpWid, resiWid])
                parms.append(td)
                
        return np.array(subImgs), np.array(parms)
    
    def removeHeaderAndOverScan(self, srcDir, fname):
        
        imgSize = (4136, 4196)
        overscanLeft = 20
        overscanRight = 80
        fullPath = "%s/%s"%(srcDir, fname)
        
        keyword=['WCSASTRM','WCSDIM','CTYPE1','CTYPE2',
                 'CRVAL1','CRVAL2','CRPIX1','CRPIX2',
                 'CD1_1','CD1_2','CD2_1','CD2_2','WAT0_001',
                 'WAT1_001','WAT1_002','WAT1_003','WAT1_004','WAT1_005','WAT1_006','WAT1_007','WAT1_008',
                 'WAT2_001','WAT2_002','WAT2_003','WAT2_004','WAT2_005','WAT2_006','WAT2_007','WAT2_008']
    
        hdul = fits.open(fullPath, mode='update', memmap=False)
        hdu1 = hdul[0]
        hdr = hdu1.header
        self.log.debug("%s skyId %s"%(fname, hdr['FIELD_ID']))
        for kw in keyword:
            hdr.remove(kw,ignore_missing=True)
        data = hdu1.data
        hdu1.data = data[:,overscanLeft:-overscanRight]
        hdul.flush()
        hdul.close()
    
    def gridStatistic(self, srcDir, catfile, imgSize, gridNum=4):
        
        catData = np.loadtxt("%s/%s"%(srcDir, catfile))
                
        #imgSize = (4136, 4196)
        #imgSize = (4136, 4096)
        imgW = imgSize[1]
        imgH = imgSize[0]
        
        tintervalW = imgW/gridNum
        tintervalH = imgH/gridNum
        
        tarray = []
        for i in range(gridNum):
            yStart = i*tintervalH
            yEnd = (i+1)*tintervalH
            for j in range(gridNum):
                xStart = j*tintervalW
                xEnd = (j+1)*tintervalW
                tnum = 0
                for row in catData:
                    tx = row[0]
                    ty = row[1]
                    if tx>=xStart and tx<xEnd and ty>=yStart and ty<yEnd:
                        tnum = tnum + 1
                    
                tarray.append((i,j,tnum))
        tnum2 = 0
        for trow in tarray:
            tnum2 = tnum2+ trow[2]
            
        tarray = np.array(tarray)
        tnum = tarray[:,2]
        tmax = np.max(tnum)
        tmin = np.min(tnum)
        tmean = np.mean(tnum)
        trms = np.std(tnum)
        
        self.log.info("%s grid total star %d:%d"%(catfile, catData.shape[0], tnum2))
        self.log.info("grid number max %.5f, min %.5f, mean %.5f, rms %.5f"%(tmax, tmin, tmean, trms))
        return tmean, tmin, trms
        
    def fwhmEvaluate(self, srcDir, catfile, size=2000):
    
        catData = np.loadtxt("%s/%s"%(srcDir, catfile))
        
        #imgSize = (4136, 4196)
        imgSize = (4136, 4096)
        imgW = imgSize[1]
        imgH = imgSize[0]
        
        halfSize = size/2
        xStart = int(imgW/2 - halfSize)
        xEnd = int(imgW/2 + halfSize)
        yStart = int(imgH/2 - halfSize)
        yEnd = int(imgH/2 + halfSize)
        
        fwhms = []
        for row in catData:
            tx = row[0]
            ty = row[1]
            fwhm = row[9]
            if tx>=xStart and tx<xEnd and ty>=yStart and ty<yEnd:
                fwhms.append(fwhm)
        
        fwhms = np.array(fwhms)
        
        times = 2
        for i in range(1):
            tmean = np.mean(fwhms)
            trms = np.std(fwhms)
            tIdx = fwhms<(tmean+times*trms)
            fwhms = fwhms[tIdx]
            
        tmean = np.mean(fwhms)
        trms = np.std(fwhms)
        
        return tmean, trms
        
    def evaluatePos(self, pos1, pos2, isAbs=False):
        
        if isAbs:
            posDiff = np.fabs(pos1 - pos2)
        else:
            posDiff = pos1 - pos2
        tmean = np.mean(posDiff, axis=0)
        tmax = np.max(posDiff, axis=0)
        tmin = np.min(posDiff, axis=0)
        trms = np.std(posDiff, axis=0)
        return tmean, trms, tmax, tmin
        
    #http://stsdas.stsci.edu/cgi-bin/gethelp.cgi?geomap
    def getMatchPosHmg(self, srcDir, oiFile, tiFile, mchPair):
        
        tdata1 = np.loadtxt("%s/%s"%(srcDir, oiFile))
        tdata2 = np.loadtxt("%s/%s"%(srcDir, tiFile))
        tIdx1 = np.loadtxt("%s/%s"%(srcDir, mchPair)).astype(np.int)
        
        tMin = np.min([tdata1.shape[0], tdata2.shape[0]])
        percentage = tIdx1.shape[0]*1.0/tMin
        
        self.log.info("getMatchPosHmg: osn16:%d tsn16:%d osn16_tsn16_cm5:%d, pect:%.3f"%(tdata1.shape[0], tdata2.shape[0],tIdx1.shape[0],percentage))
        
        if percentage>0.6:
            tIdx1 = tIdx1 - 1
            pos1 = tdata1[tIdx1[:,0]][:,0:2]
            pos2 = tdata2[tIdx1[:,1]][:,0:2]
            
            dataOi = pos1
            dataTi = pos2
                
            h, tmask = cv2.findHomography(dataOi, dataTi, cv2.RANSAC, 0.1) #0, RANSAC , LMEDS
            
            dataTi2 = cv2.perspectiveTransform(np.array([dataOi]), h)
            dataTi2 = dataTi2[0]
            
            tmean, trms, tmax, tmin = self.evaluatePos(dataOi, dataTi2)
            tmean2, trms2, tmax2, tmin2 = self.evaluatePos(dataTi, dataTi2, True)
            
            xshift = tmean[0]
            yshift = tmean[1]
            xrms = trms2[0]
            yrms = trms2[1]
        else:
            h, xshift, yshift, xrms, yrms = [], 0, 0, 99, 99
            tmsgStr = "pos match error: percentage %.2f%%"%(percentage*100)
            self.log.error(tmsgStr)
        
        return h, xshift, yshift, xrms, yrms
    
    def imageAlign2(self, srcDir, oiFile, tiFile, mchPair):
    
        starttime = datetime.datetime.now()
        
        h, xshift, yshift = self.getMatchPos(srcDir, oiFile, tiFile, mchPair)
        
        tpath = "%s/%s"%(srcDir, oiFile)
        tData = fits.getdata(tpath)
        newimage = cv2.warpPerspective(tData, h, (tData.shape[1],tData.shape[0]))
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("opencv remap sci image use %.2f seconds"%(runTime))
        
        return newimage, h, xshift, yshift
        
    def imageAlignHmg(self, srcDir, oiImg, transHG):
    
        starttime = datetime.datetime.now()
                
        tpath = "%s/%s"%(srcDir, oiImg)
        tData = fits.getdata(tpath)
        newimage = cv2.warpPerspective(tData, transHG, (tData.shape[1],tData.shape[0]))
        
        newName = "new.fit"
        newPath = "%s/%s"%(srcDir, newName)
        if os.path.exists(newPath):
            os.remove(newPath)
        hdu = fits.PrimaryHDU(newimage)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath)
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("opencv remap sci image use %.2f seconds"%(runTime))
        
        return newName
        
    def catShift(self, srcDir, fileName, xshift0, yshift0, transHG):
    
        tdata = np.loadtxt("%s/%s"%(srcDir, fileName))
        if len(transHG)>0:
            txy = tdata[:,0:2]
            txy = cv2.perspectiveTransform(np.array([txy]), transHG)
            txy = txy[0]
            tdata[:,0] = txy[:,0]
            tdata[:,1] = txy[:,1]
        else:
            tdata[:,0] = tdata[:,0] - xshift0
            tdata[:,1] = tdata[:,1] - yshift0
        
        tpre= fileName.split(".")[0]
        saveName = "%s_s.cat"%(tpre)
        savePath = "%s/%s"%(srcDir, saveName)
        np.savetxt(savePath, tdata, fmt='%.5f',delimiter=' ')
        
        return saveName
    
    def processBadPix(self, objName, bkgName, srcPath, dstPath):
        
        starttime = datetime.datetime.now()
        
        objPath = "%s/%s"%(srcPath, objName)
        bkgPath = "%s/%s"%(srcPath, bkgName)
        
        objData = fits.getdata(objPath)
        bkgData = fits.getdata(bkgPath)
        
        tIdx = objData<bkgData
        bkgData[tIdx] = objData[tIdx]
        bkgMax = np.max(bkgData)
        
        bkgData = 1 + bkgMax -bkgData
        '''
        newName = "badpix1.fit"
        newPath = "%s/%s"%(dstPath, newName)
        if os.path.exists(newPath):
            os.remove(newPath)
        hdu = fits.PrimaryHDU(bkgData)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath)
        '''
        
        starttime1 = datetime.datetime.now()
        bkgData = bkgData.astype(np.uint16)
        #bkgData = mean(bkgData, square(3))
        #kernel = np.ones((3,3),np.float32)/25
        #dst = cv2.filter2D(bkgData,-1,kernel)
        bkgData = cv2.blur(bkgData,(3,3)) #faster than mean
        bkgData = bkgData.astype(np.uint16)
        
        endtime1 = datetime.datetime.now()
        runTime1 = (endtime1 - starttime1).seconds
        self.log.debug("process badpix meanfilter use %d seconds"%(runTime1))
        
        newName = "badpix.fit"
        newPath = "%s/%s"%(srcPath, newName)
        if os.path.exists(newPath):
            os.remove(newPath)
        hdu = fits.PrimaryHDU(bkgData)
        hdul = fits.HDUList([hdu])
        hdul.writeto(newPath)
    
        fpar='sex_diff.par'
        sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
        resultCat = self.runSextractor(newName, srcPath, srcPath, fpar, sexConf)
        
        tdata = np.loadtxt("%s/%s"%(srcPath, resultCat))
        
        fluxMax = tdata[:,4] #FLUX_MAX
        fluxMaxMean = np.mean(fluxMax)
        fluxMaxStd = np.std(fluxMax)
        fluxMaxThd = fluxMaxMean+1.0*fluxMaxStd #2σ:0.9544, 1.5σ:0.866, 1σ:0.682
        tidx = fluxMax>fluxMaxThd 
        self.log.info("badpix star %d, fluxMaxMean=%.2f, fluxMaxStd=%.2f, fluxMaxThd=%.2f"%(tdata.shape[0], fluxMaxMean, fluxMaxStd, fluxMaxThd))
        
        tdata = tdata[tidx]
        
        self.log.debug("badpix flux_max>background star %d"%(tdata.shape[0]))
        ds9RegionName = "%s/%s_ds9.reg"%(srcPath, resultCat[:resultCat.index(".")])
        with open(ds9RegionName, 'w') as fp1:
            for tobj in tdata:
               fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%ld-%.2f} font=\"times 10\"\n"%
               (tobj[0], tobj[1], 4.0, tobj[4], tobj[8]))
        
        selposName = "%s_sel.cat"%(resultCat[:resultCat.index(".")])
        selposPath = "%s/%s"%(srcPath, selposName)
        with open(selposPath, 'w') as fp1:
            for tobj in tdata:
               fp1.write("%.3f %.3f %.3f\n"%(tobj[0], tobj[1], tobj[11]))
        
        endtime = datetime.datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("process badpix use %d seconds"%(runTime))
        
        return selposName
        
    '''
    选择部分假OT，过滤条件：
    1）过滤最暗的和最亮的（3%）
    2）过滤图像边缘的fSize（200px）
    '''
    def filtOTs(fname, tpath, darkMagRatio=0.03, brightMagRatio=0.03,fSize=100, imgSize=(4136, 4096)):
    
        tdata = np.loadtxt("%s/%s"%(tpath, fname))
        
        minX = 0 + fSize
        minY = 0 + fSize
        maxX = imgSize[0] - fSize
        maxY = imgSize[1] - fSize
    
        mag = tdata[:,12]
        mag = np.sort(mag)
        maxMag = mag[int((1-darkMagRatio)*tdata.shape[0])]
        minMag = mag[int(brightMagRatio*tdata.shape[0])]
                
        tobjs = []
        for obj in tdata:
            
            tx = obj[1]
            ty = obj[2]
            tmag = obj[12]
            ts2n = 1.087/obj[13]
            if tx>minX and tx <maxX and ty>minY and ty<maxY and tmag<maxMag and tmag>minMag:
                tobjs.append([tx, ty, tmag, ts2n])
                
        outCatName = "%sf.cat"%(fname[:fname.index(".")])
        outCatPath = "%s/%s"%(tpath, outCatName)
        with open(outCatPath, 'w') as fp0:
            for tobj in tobjs:
               fp0.write("%.2f %.2f %.2f %.2f\n"%(tobj[0], tobj[1], tobj[2], tobj[3]))
        
        ds9RegionName = "%s/%s_filter_ds9.reg"%(tpath, fname[:fname.index(".")])
        with open(ds9RegionName, 'w') as fp1:
            for tobj in tobjs:
               fp1.write("image;circle(%.2f,%.2f,%.2f) # color=green width=1 text={%.2f} font=\"times 10\"\n"%
               (tobj[0], tobj[1], 4.0, tobj[2]))
               
        return outCatName
        
    def sendTriggerMsg(self, tmsg):

        try:
            msgURL = "http://172.28.8.8:8080/gwebend/sendTrigger2WChart.action?chatId=gwac004&triggerMsg="
            turl = "%s%s"%(msgURL,tmsg)
            
            msgSession = requests.Session()
            msgSession.get(turl, timeout=10, verify=False)
        except Exception as e:
            self.log.error(" send trigger msg error ")
            self.log.error(str(e))