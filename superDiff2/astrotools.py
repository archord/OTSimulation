# -*- coding: utf-8 -*-
import numpy as np
import os
import math
import subprocess
from datetime import datetime
import cv2
from astropy.io import fits
import warnings
import traceback
import time
import logging
import requests
from astropy.modeling import models, fitting
import paramiko


class AstroTools(object):
    
    def __init__(self, rootPath, logFile="gwac_diff"): 
        
        self.verbose = False
        
        self.serverIP = "http://172.28.8.8:8080"
        #self.serverIP = "http://10.0.10.236:9995"
        #self.serverIP = "http://10.36.1.77:8080"
        
        self.rootPath = rootPath
        self.varDir = "%s/tools/simulate_tools"%(rootPath)
        self.matchProgram="%s/tools/CrossMatchLibrary/dist/Debug/GNU-Linux/crossmatchlibrary"%(rootPath)
        self.imgDiffProgram="%s/tools/hotpants/hotpants"%(rootPath)
        self.funpackProgram="%s/tools/cfitsio/funpack"%(rootPath)
        #self.wcsProgram="%s/tools/astrometry.net/bin/solve-field"%(rootPath)
        self.wcsProgram="solve-field"
        self.wcsProgramPC780="/home/xy/Downloads/myresource/deep_data2/image_diff/tools/astrometry.net/bin/solve-field"
    
        os.environ['VER_DIR'] = self.varDir
                
        self.initLog(logFile)
        
    def initLog(self, logFile):
        
        self.log = logging.getLogger() #create logger
        self.log.setLevel(logging.INFO) #set level of logger, DEBUG INFO
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s") #set format of logger
        logging.Formatter.converter = time.gmtime #convert time in logger to UCT
        filehandler = logging.FileHandler("%s/%s.log"%(self.rootPath, logFile), 'w+')
        filehandler.setFormatter(formatter) #add format to log file
        self.log.addHandler(filehandler) #link log file to logger
        if self.verbose:
            streamhandler = logging.StreamHandler() #create print to screen logging
            streamhandler.setFormatter(formatter) #add format to screen logging
            self.log.addHandler(streamhandler) #link logger to screen logging
        
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
    
    def runWCS(self, srcDir, objCat, ra, dec, radius=10, width=4096, height=4136):
    
        self.log.info('Executing run_wcs ...')
        
        runSuccess = True
        astronet_tweak_order = 3
        scale_low = 0.98
        scale_high = 1.02
        astronet_radius = radius
        
        baseName = objCat.split('.')[0]
        srcPath = "%s/%s"%(srcDir, objCat)
    
        #scampcat = image_in.replace('.fits','.scamp')
        cmd = [self.wcsProgram, srcPath, 
               '--cpulimit', '60'
               '--no-plots', '--no-verify', #'--no-fits2fits', cloud version of astrometry does not have this arg
               '--x-column', 'X_IMAGE', '--y-column', 'Y_IMAGE',
               '--sort-column', 'FLUX_APER',
               '--no-remove-lines', '--uniformize', '0',
               # only work on brightest sources
               '--objs', '1000',
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
               '--tweak-order', str(astronet_tweak_order), 
               #'--scale-low', str(scale_low),
               #'--scale-high', str(scale_high), '--scale-units', 'app',
               '--ra', str(ra), '--dec', str(dec), '--radius', str(astronet_radius),
               '--overwrite'
        ]
        
        self.log.debug(cmd)
        
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        self.log.debug(stdoutstr)
        self.log.debug(stderrstr)
                
        wcsfile = baseName+'.wcs'
        wcsPath = "%s/%s"%(srcDir, wcsfile)
        if not os.path.exists(wcsPath):
            self.log.error("astrometry failed.")
            runSuccess = False
        
        return runSuccess
    
    def remoteGetFile(self, srcFiles, destDir, user='gwac', pwd='xyag902', ip='172.28.8.8'):
        
        self.log.info('remote get files ...')
    
        runSuccess = True
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(ip, username=user, password=pwd)
            ftp = ssh.open_sftp()
            for tfile in srcFiles:
                ftp.get(tfile,"%s/%s"%(destDir,tfile.split('/')[-1]))
        except paramiko.AuthenticationException:
            self.log.error("Authentication Failed!")
            runSuccess = False
            tstr = traceback.format_exc()
            self.log.error(tstr)
        except paramiko.SSHException:
            self.log.error("Issues with SSH service!")
            runSuccess = False
            tstr = traceback.format_exc()
            self.log.error(tstr)
        except Exception as e:
            self.log.error(str(e))
            runSuccess = False
            tstr = traceback.format_exc()
            self.log.error(tstr)
        
        try:
            time.sleep(1)
            ftp.close()
            ssh.close()
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            self.log.error(tstr)
        
        return runSuccess
        

    def runWCSRemotePC780(self, srcDir, objCat, ra, dec, ccdName, width=4096, height=4136):
    
        self.log.info('Executing run_wcs remotely ...')
    
        runSuccess = True
        baseName = objCat.split('.')[0]
        wcsfile = baseName+'.wcs'
            
        sftpUser  =  'xy'
        sftpPass  =  'l'
        pc870 = '10.36.1.211'
        wcsParm1 = " --no-plots --no-verify --x-column X_IMAGE --y-column Y_IMAGE --sort-column FLUX_APER --objs 1000 --overwrite " \
            "--no-remove-lines --uniformize 0 --depth 50,150,200,250,300,350,400,450,500 "
                
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
            
        runSuccess = True
        astronet_tweak_order = 5
        astronet_radius = 20
        try:
            remoteSrcRoot = "/run/shm/gwacwcs/%s"%(ccdName)
            remoteSrcPath = "%s/%s"%(remoteSrcRoot,objCat)
            srcPath = "%s/%s"%(srcDir, objCat)
            remoteWcsPath = "%s/%s"%(remoteSrcRoot,wcsfile)
            wcsPath = "%s/%s"%(srcDir, wcsfile)
            
            ssh.connect(pc870, username=sftpUser, password=sftpPass)
            tcmd = "rm -rf %s;mkdir -p %s;"%(remoteSrcRoot,remoteSrcRoot)
            stdin, stdout, stderr = ssh.exec_command(tcmd, get_pty=True)
            for line in iter(stdout.readline, ""):
                self.log.debug(line)
            
            ftp = ssh.open_sftp()
            ftp.put(srcPath,remoteSrcPath)
            
            wcsParm2 = "--width %d --height %d --tweak-order %d --ra %f --dec %f --radius %f"%(width, height, astronet_tweak_order, ra, dec, astronet_radius)
            wcsCMD = "%s %s %s %s"%(self.wcsProgramPC780, remoteSrcPath, wcsParm1, wcsParm2)
            self.log.info(wcsCMD)
            stdin, stdout, stderr = ssh.exec_command(wcsCMD, get_pty=True)
            for line in iter(stdout.readline, ""):
                self.log.debug(line)
            
            ftp.chdir(remoteSrcRoot)
            tfiles = ftp.listdir()
            tfiles.sort()
            remoteWCSExist = False
            for tfile in tfiles:
                if tfile==wcsfile:
                    remoteWCSExist=True
                    break
            if remoteWCSExist:
                ftp.get(remoteWcsPath,wcsPath)
                
            if (not remoteWCSExist) or (not os.path.exists(wcsPath)):
                self.log.error("astrometry failed.")
                runSuccess = False
            else:
                self.log.info("astrometry success.")
                    
        except paramiko.AuthenticationException:
            self.log.error("Authentication Failed!")
            runSuccess = False
            tstr = traceback.format_exc()
            self.log.error(tstr)
        except paramiko.SSHException:
            self.log.error("Issues with SSH service!")
            runSuccess = False
            tstr = traceback.format_exc()
            self.log.error(tstr)
        except Exception as e:
            self.log.error(str(e))
            runSuccess = False
            tstr = traceback.format_exc()
            self.log.error(tstr)
        
        try:
            time.sleep(1)
            ftp.close()
            ssh.close()
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            self.log.error(tstr)
        
        return runSuccess
        
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
                      cmdStatus=1, outSuffix='.cat'):
        isSuccess = False
        starttime = datetime.now()
        
        outpre= fname.split(".")[0]
        fullPath = "%s/%s"%(srcPath, fname)
        cnfPath = "%s/config/%s"%(self.varDir, fconf)
        outParmPath = "%s/config/%s"%(self.varDir, fpar) #sex_diff.par  OTsearch.par  sex_diff_fot.par
        
        outFile = "%s%s"%(outpre, outSuffix)
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
        #if os.path.exists(outFPath):
            self.log.debug("run sextractor success.")
            self.log.debug("generate catalog %s"%(outFPath))
            isSuccess = True
        else:
            self.log.error("sextractor failed.")
            isSuccess = False
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("run sextractor use %d seconds"%(runTime))
            
        return outFile, isSuccess
    
        #hotpants
    def runHotpants(self, objImg, tmpImg, srcDir):
        
        starttime = datetime.now()
        runSuccess = True        
        
        objpre= objImg.split(".")[0]
        tmppre= tmpImg.split(".")[0]
        objFPath = "%s/%s"%(srcDir, objImg)
        tmpFPath = "%s/%s"%(srcDir, tmpImg)
        outFile = "%s_%s_resi.fit"%(objpre,tmppre)
        outFPath = "%s/%s"%(srcDir, outFile)
        
        # run sextractor from the unix command line
        #/home/xy/program/C/hotpants/hotpants -inim oi.fit -tmplim ti.fit -outim oi_ti_resi.fit -v 0 -nrx 4 -nry 4
        cmd = [self.imgDiffProgram, '-inim', objFPath, '-tmplim', tmpFPath, '-outim', 
                 outFPath, '-v', '0', '-nrx', '4', '-nry', '4', '-nsx', '6', '-nsy', '6', '-r', '6',
                 '-tu','50000','-iu','500000','-nss','6','-ko','4','-bgo','1']
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        
        if os.path.exists(outFPath) and status==0:
            self.log.debug("run hotpants success.")
            self.log.debug("generate diff residual image %s"%(outFPath))
            runSuccess = True
        else:
            self.log.error("hotpants failed.")
            self.log.info(stdoutstr)
            self.log.info(stderrstr)
            runSuccess = False
            
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("run hotpants use %d seconds"%(runTime))
            
        return outFile, runSuccess
    
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
        
        try:
            fieldId = hdr['FIELD_ID']
            ra = hdr['RA']
            dec = hdr['DEC']
        except Exception as e:
            fieldId = '0'
            ra = 0
            dec = 0
            tstr = traceback.format_exc()
            self.log.error(tstr)
            
        for kw in keyword:
            hdr.remove(kw,ignore_missing=True)
        data = hdu1.data
        hdu1.data = data[:,overscanLeft:-overscanRight]
        hdul.flush()
        hdul.close()
        
        return fieldId, ra,dec
        
    def getRaDec(self, srcDir, fname):
        
        fullPath = "%s/%s"%(srcDir, fname)
    
        hdul = fits.open(fullPath)
        hdu1 = hdul[0]
        hdr = hdu1.header
        try:
            fieldId = hdr['FIELD_ID']
            ra = hdr['RA']
            dec = hdr['DEC']
        except Exception as e:
            fieldId = '0'
            ra = 0
            dec = 0
            tstr = traceback.format_exc()
            self.log.error(tstr)
        hdul.close()
        
        return fieldId, ra,dec
    
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
        
    def basicStatistic(self, srcDir, catfile, size=2000):
        
        tpath = "%s/%s"%(srcDir, catfile)
        try:
            catData = np.loadtxt(tpath)
            starNum = catData.shape[0]
            
            #imgSize = (4136, 4196)
            imgSize = (2400, 2400)
            imgW = imgSize[1]
            imgH = imgSize[0]
            
            halfSize = size/2
            xStart = int(imgW/2 - halfSize)
            xEnd = int(imgW/2 + halfSize)
            yStart = int(imgH/2 - halfSize)
            yEnd = int(imgH/2 + halfSize)
            
            fwhms = []
            bgs = []
            for row in catData:
                tx = row[0]
                ty = row[1]
                bg = row[8]
                fwhm = row[9]
                if tx>=xStart and tx<xEnd and ty>=yStart and ty<yEnd:
                    fwhms.append(fwhm)
                    bgs.append(bg)
            
            fwhms = np.array(fwhms)
            bgs = np.array(bgs)
            
            times = 2
            for i in range(1):
                tmean = np.mean(fwhms)
                trms = np.std(fwhms)
                tIdx = fwhms<(tmean+times*trms)
                fwhms = fwhms[tIdx]
                
                tmean = np.mean(bgs)
                trms = np.std(bgs)
                tIdx = bgs<(tmean+times*trms)
                bgs = bgs[tIdx]
                
            fwhmMean = np.mean(fwhms)
            fwhmRms = np.std(fwhms)
            bgMean = np.mean(bgs)
            bgRms = np.std(bgs)
        
            return starNum, fwhmMean, fwhmRms, bgMean, bgRms
        except Exception as e:
                        
            self.log.error("basicStatistic error %s"%(tpath))
            self.log.error(str(e))
            tstr = traceback.format_exc()
            self.log.error(tstr)
            return 0,0,0,0,0
        
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
    
        starttime = datetime.now()
        
        h, xshift, yshift = self.getMatchPos(srcDir, oiFile, tiFile, mchPair)
        
        tpath = "%s/%s"%(srcDir, oiFile)
        tData = fits.getdata(tpath)
        newimage = cv2.warpPerspective(tData, h, (tData.shape[1],tData.shape[0]))
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("opencv remap sci image use %.2f seconds"%(runTime))
        
        return newimage, h, xshift, yshift
        
    def imageAlignHmg(self, srcDir, oiImg, oiCat, transHG):
    
        starttime = datetime.now()
        
        tdata1 = np.loadtxt("%s/%s"%(srcDir, oiCat))
        pos1 = tdata1[:,0:2].copy()  ## orig X Y
        pos2 = cv2.perspectiveTransform(np.array([pos1]), transHG)
        pos2 = pos2[0] # temp X Y
        tdata1[:,0]=pos2[:,0]
        tdata1[:,1]=pos2[:,1]
        
        outCatName = "%s_trans.cat"%(oiCat[:oiCat.index(".")])
        outCatPath = "%s/%s"%(srcDir, outCatName)
        tstr=""
        i=0
        for td in tdata1:
           tstr += "%.4f %.4f %.2f %.2f %.2f %.3f %.3f %.3f %.2f %.2f %d %.4f %.4f %.4f %.4f\n"%\
              (td[0],td[1],td[2],td[3],td[4],td[5],td[6],td[7],td[8],td[9],td[10],td[11],td[12], pos1[i][0], pos1[i][1])
           i=i+1
        fp0 = open(outCatPath, 'w')
        fp0.write(tstr)
        fp0.close()
                
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
        
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.debug("opencv remap sci image use %.2f seconds"%(runTime))
        
        return newName, outCatName
        
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
        
        starttime = datetime.now()
        
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
        
        starttime1 = datetime.now()
        bkgData = bkgData.astype(np.uint16)
        #bkgData = mean(bkgData, square(3))
        #kernel = np.ones((3,3),np.float32)/25
        #dst = cv2.filter2D(bkgData,-1,kernel)
        bkgData = cv2.blur(bkgData,(3,3)) #faster than mean
        bkgData = bkgData.astype(np.uint16)
        
        endtime1 = datetime.now()
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
        resultCat, isSuccess = self.runSextractor(newName, srcPath, srcPath, fpar, sexConf)
        if not isSuccess:
            print("processBadPix runSextractor failure1")
            return ''
        
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
            for td in tdata:
               #fp1.write("%.3f %.3f %.3f\n"%(td[0], td[1], td[11]))
               tstr = "%.4f %.4f %.2f %.2f %.2f %.3f %.3f %.3f %.2f %.2f %d %.4f %.4f\n"%\
                  (td[0],td[1],td[2],td[3],td[4],td[5],td[6],td[7],td[8],td[9],td[10],td[11],td[12])
               fp1.write(tstr)
        
        endtime = datetime.now()
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
        
    def getBright(self, tpath, fname, brightMagRatio=0.5):
    
        tdata = np.loadtxt("%s/%s"%(tpath, fname))
            
        mag = tdata[:,12]
        mag = np.sort(mag)
        maxMag = mag[int(brightMagRatio*tdata.shape[0])]
                
        tdata = tdata[tdata[:,12]<maxMag]
                
        outCatName = "%s_fp%02d.cat"%(fname[:fname.index(".")], int(brightMagRatio*100))
        outCatPath = "%s/%s"%(tpath, outCatName)
        with open(outCatPath, 'w') as fp0:
            for td in tdata:
               tstr = "%.4f %.4f %.2f %.2f %.2f %.3f %.3f %.3f %.2f %.2f %d %.4f %.4f\n"%\
                  (td[0],td[1],td[2],td[3],td[4],td[5],td[6],td[7],td[8],td[9],td[10],td[11],td[12])
               fp0.write(tstr)
               
        return outCatName
        
    def sendTriggerMsg(self, tmsg):

        try:
            sendTime = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
            tmsg = "%s\n %s"%(sendTime, tmsg)
            msgURL = "%s/gwebend/sendTrigger2WChart.action?chatId=gwac004&triggerMsg="%(self.serverIP)
            turl = "%s%s"%(msgURL,tmsg)
            
            msgSession = requests.Session()
            msgSession.get(turl, timeout=10, verify=False)
        except Exception as e:
            self.log.error(" send trigger msg error ")
            self.log.error(str(e))
            tstr = traceback.format_exc()
            self.log.error(tstr)
