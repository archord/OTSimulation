# -*- coding: utf-8 -*-
import numpy as np
import os
import sys
import math
import time
import subprocess
from datetime import datetime
import traceback
from PIL import Image
import scipy.ndimage
from astropy.wcs import WCS
from astropy.time import Time
from astropy.io import fits
import requests

from gwac_util import getThumbnail, genPSFView, getWindowImgs, getLastLine, selectTempOTs, filtOTs, filtByEllipticity, getDs9Reg
from astrotools import AstroTools
from ot2classify import OT2Classify
            
class BatchImageSim(object):
    def __init__(self, dataRoot, dataDest, tools, camName, skyName): 
        
        self.camName = camName
        self.skyName = str(skyName)
        self.ffNumber = 0
        self.toolPath = os.getcwd()
        self.funpackProgram="%s/tools/cfitsio/funpack"%(self.toolPath)
        self.tmpRoot="/dev/shm/gwacsim2"
        self.tmpUpload="/dev/shm/gwacupload"
        self.tmpDir="%s/tmp"%(self.tmpRoot)
        self.tmpCat="%s/cat"%(self.tmpRoot)
        self.templateDir="%s/tmpl"%(self.tmpRoot)
        self.modelPath="%s/tools/mlmodel"%(self.toolPath)
        
        #self.dataRoot = "/data/gwac_data"
        self.srcDir0 = "%s"%(dataRoot)
        self.srcDir = "%s"%(dataRoot)
            
        self.objectImg = 'oi.fit'
        self.templateImg = 'ti.fit'
        self.objectImgSim = 'ois.fit'
        self.objTmpResi = 'otr.fit'
        self.simTmpResi = 'str.fit'
        self.newImageName = "new.fit"
        
        self.badPixCat = 'badpix.cat'
        self.objectImgSimAdd = 'oisa.cat'
        self.objectImgCat = 'oi.cat'
        self.templateImgCat = 'ti.cat'
        self.objectImgSimCat = 'ois.cat'
        self.objTmpResiCat = 'otr.cat'
        self.simTmpResiCat = 'str.cat'
        
        self.imgSize = (4136, 4096)
        self.subImgSize = 21
        self.imgShape = []  
             
        self.selTemplateNum = 10 # 10 3
        self.maxFalseNum = 5
        
        self.sendUrl = "http://172.28.8.8/gwebend/regOrigImg.action"
        
        self.tools = tools
        self.log = tools.log
        #self.modelName='model_80w_20190403_branch3_train12_79.h5'
        self.modelName='model_RealFOT_64_100_fot10w_20190122_dropout.h5'
        self.ot2Classifier = OT2Classify(self.toolPath, self.log, self.modelName)
        
        self.initReg(0)

    def sendMsg(self, tmsg):
        
        tmsgStr = "%s, sky:%s, ffNum:%d\n %s"%(self.camName, self.skyName, self.ffNumber, tmsg)
        self.tools.sendTriggerMsg(tmsgStr)
    
    def initReg(self, idx):
        
        if idx<=0:
            idx =0
            os.system("rm -rf %s/*"%(self.tmpRoot))
            os.system("rm -rf %s/*"%(self.tmpUpload))
            if not os.path.exists(self.tmpUpload):
                os.system("mkdir -p %s"%(self.tmpUpload))
            if not os.path.exists(self.templateDir):
                os.system("mkdir -p %s"%(self.templateDir))
            if not os.path.exists(self.tmpDir):
                os.system("mkdir -p %s"%(self.tmpDir))
            if not os.path.exists(self.tmpCat):
                os.system("mkdir -p %s"%(self.tmpCat))
        
        self.procNum = 0
        self.tmplImgIdx = 0 
        self.regFalseNum = 0
        self.regSuccessNum = 0
        self.diffFalseNum = 0
        self.origTmplImgName = ""
        self.regFalseIdx = 0
        self.makeTempFalseNum = 0
        self.imglist = []
        self.transHGs = []

    def regImg2DB(self, tpath, objFits):
        
        objPath = "%s/%s"%(tpath, objFits)
        
        try:
            with fits.open(objPath,memmap=False) as ft:
                theader = ft[0].header
                #theader = fits.getheader(objPath, 0)
                groupId = theader['GROUP_ID']
                unitID = theader['UNIT_ID']
                camID = theader['CAM_ID']
                gridID = theader['GRID_ID']
                fieldID = theader['FIELD_ID']
                tdate = theader['DATE-OBS']
                ttime = theader['TIME-OBS']
                genTime = "%sT%s"%(tdate, ttime)
                imgName = objFits
                imgPath = tpath
                
                values = {'groupId': groupId, 'unitId': unitID, 'camId': camID,
                          'gridId': gridID, 'fieldId': fieldID, 'genTime': genTime, 
                          'imgName': imgName, 'imgPath': imgPath}
                print(values)
                r = requests.post(self.sendUrl, data=values)
                print(r.text)
        except Exception as e:
            print(e)
        
        return True
            
    def getRaDec(self, objCat):
        
        tpre= objCat.split(".")[0]
        saveName = "%s_objxy.cat"%(tpre)
        saveName1 = "%s_objsky.cat"%(tpre)
        catOutPath = "%s/%s"%(self.tmpDir, saveName1)
        fitsPath = "%s/%s"%(self.tmpDir, self.objectImg)
        catInPath = "%s/%s"%(self.tmpDir, saveName)
        
        tdata = np.loadtxt("%s/%s"%(self.tmpDir, objCat))
        txy = tdata[:,0:2]
        savePath = "%s/%s"%(self.tmpDir, saveName)
        np.savetxt(savePath, txy, fmt='%.5f',delimiter=' ')
        
        #tnx2sky <path of fits> <input file> <output file>
        cmd = ['tnx2sky', fitsPath, catInPath, catOutPath]
        self.log.debug(cmd)
           
        # run command
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdoutstr,stderrstr) = process.communicate()
        status = process.returncode
        
        if os.path.exists(catOutPath) and status==0:
            self.log.debug("cat align success.")
            self.log.debug("generate aligned file1 %s"%(saveName1))
        else:
            self.log.error("cat align failed.")
        
        tdata2 = np.loadtxt(catOutPath)
        tdata3 = np.concatenate((tdata, txy, tdata2[:,2:4]), axis=1)
        saveName3 = "%s_trans.cat"%(tpre)
        savePath = "%s/%s"%(self.tmpDir, saveName3)
        np.savetxt(savePath, tdata3, fmt='%.5f',delimiter=' ')
        
        return saveName3
        
    def diff(self, srcDir, destDir, tmpFit, objFits, reverse=False):
                
        try:
            if not os.path.exists(destDir):
                os.system("mkdir -p %s"%(destDir))
                
            self.regImg2DB(srcDir, tmpFit)
                
            os.system("rm -rf %s/*"%(self.templateDir))
            os.system("cp %s/%s %s/%s"%(srcDir, tmpFit, self.templateDir, self.templateImg))
            
            for i, imgName in enumerate(objFits):
                
                starttime = datetime.now()
                self.log.info("diff %d: %s"%(i, imgName))
                
                self.regImg2DB(srcDir, imgName)
                
                os.system("rm -rf %s/*"%(self.tmpDir))
                imgpre= imgName.split(".")[0]
                tobjFitsFullPath = "%s/%s.fit"%(srcDir, imgpre)
                if not os.path.exists(tobjFitsFullPath):
                    self.log.error("%s.fit not exist, stop"%(imgpre))
                    break
                
                if os.path.exists("%s/diffResi/%s.fit"%(destDir, imgpre)):
                    self.log.info("%s.fit already diffed, skip"%(imgpre))
                    continue
                
                os.system("cp %s/%s.fit %s/%s"%(srcDir, imgpre, self.tmpDir, self.objectImg))
                os.system("cp %s/%s %s/%s"%(self.templateDir, self.templateImg, self.tmpDir, self.templateImg))
                
                self.objTmpResi, runSuccess = self.tools.runHotpants(self.objectImg, self.templateImg, self.tmpDir)
                if not runSuccess:
                    self.log.info("%s.fit diff error..."%(imgpre))
                    continue
        
                if reverse:
                    os.system("cp %s/%s %s/diffResi/%s_r.fit"%(self.tmpDir, self.objTmpResi, destDir, imgpre))
                else:
                    os.system("cp %s/%s %s/diffResi/%s.fit"%(self.tmpDir, self.objTmpResi, destDir, imgpre))
                
                
                tgrid = 4
                tsize = 500
                tzoom = 2
                timg = getThumbnail(self.tmpDir, self.objTmpResi, stampSize=(tsize,tsize), grid=(tgrid, tgrid), innerSpace = 1)
                timg = scipy.ndimage.zoom(timg, tzoom, order=0)
                if reverse:
                    preViewPath = "%s/preview/%s_resi_r.jpg"%(destDir, imgpre)
                else:
                    preViewPath = "%s/preview/%s_resi.jpg"%(destDir, imgpre)
                Image.fromarray(timg).save(preViewPath)
                
                fpar='sex_diff.par'
                sexConf=['-DETECT_MINAREA','3','-DETECT_THRESH','2.5','-ANALYSIS_THRESH','2.5']
                resiCat = self.tools.runSextractor(self.objTmpResi, self.tmpDir, self.tmpDir, fpar, sexConf)
                resiCatTrans = self.getRaDec(resiCat)
                
                objProps = np.loadtxt("%s/%s"%(self.tmpDir, resiCatTrans))
                tstr = "%s,  resi objs %d"%(imgName, objProps.shape[0])
                self.log.info(tstr)
                
                #size = self.subImgSize
                size = 68
                if objProps.shape[0]<20000 and objProps.shape[0]>0:
                    
                    totSubImgs, totParms = getWindowImgs(self.tmpDir, self.objectImg, self.templateImg, self.objTmpResi, objProps, size)
                    if totParms.shape[0]>0:
                        #tXY = totParms[:,0:2]
                        #tRaDec = self.wcs.all_pix2world(tXY, 1)
                        #totParms = np.concatenate((totParms, tRaDec), axis=1)
                        if reverse:
                            fotpath = '%s/subImgs/%s_r.npz'%(destDir, imgpre)
                        else:
                            fotpath = '%s/subImgs/%s.npz'%(destDir, imgpre)
                        np.savez_compressed(fotpath, imgs=totSubImgs, parms=totParms)
                        
                        self.classifyAndUpload(destDir, imgName, reverse=reverse)
                        
                endtime = datetime.now()
                runTime = (endtime - starttime).seconds
                self.log.info("diff: %s use %d seconds"%(imgName, runTime))
                
                #break
        
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)
    
    def classifyAndUpload(self, destDir, imgName, reverse=False):
        
        oImgPre = imgName[:imgName.index(".")]
        upDir = "%s/%s"%(self.tmpUpload, oImgPre)
        if not os.path.exists(upDir):
            os.system("mkdir -p %s"%(upDir))
        
        os.system("cp %s/%s %s/%s"%(self.tmpDir, self.objectImg, upDir, self.objectImg))
        os.system("cp %s/%s %s/%s"%(self.tmpDir, self.templateImg, upDir, self.templateImg))
        os.system("cp %s/%s %s/%s"%(self.tmpDir, self.objTmpResi, upDir, self.objTmpResi))
        
        if reverse:
            totImgsName = '%s_r.npz'%(oImgPre)
        else:
            totImgsName = '%s.npz'%(oImgPre)
        fotImgsName = ''

        self.ot2Classifier.doClassifyAndUpload('%s/subImgs'%(destDir), totImgsName, fotImgsName, 
                          upDir, self.objectImg, self.templateImg, self.objTmpResi, 
                          imgName, self.tools.serverIP, reverse=reverse)
                          
    def batchDiff(self, srcDir, destDir, pattern='_2_c.fit', reverse=False):
        
        tfiles0 = os.listdir(srcDir)
        tfiles0.sort()
        if reverse:
            tfiles0.reverse()

        objFieldId = ''
        tfiles1 = []
        tfileds = []
        uniqueFields = []
        for tfile in tfiles0:
            if tfile.find(pattern)>-1:
                tfieldId = fits.getval("%s/%s"%(srcDir, tfile), 'FIELD_ID', 0)
                tfileds.append(tfieldId)
                tfiles1.append(tfile)
                if len(objFieldId)==0 or objFieldId != tfieldId:
                    objFieldId = tfieldId
                    uniqueFields.append(objFieldId)
        
        self.log.info(uniqueFields)
        tfileds = np.array(tfileds)
        tfiles1 = np.array(tfiles1)
        for tf in uniqueFields:
            tfiles =  tfiles1[tfileds==tf]
            if len(tfiles)>=2:
                tfiles.sort()
                tmpFit = tfiles[0]
                objFits = tfiles[1:]
                self.log.info('field %s, total %d'%(tfieldId, len(objFits)))
                self.diff(srcDir, destDir, tmpFit, objFits, reverse=reverse)
        
    def process(self, srcDir, destDir):
        
        try:
            
            tfiles0 = os.listdir(srcDir)
            tfiles0.sort()
            
            for tfile in tfiles0:
                sDirs = "%s/%s"%(srcDir, tfile)
                dDirs = "%s/%s"%(destDir, tfile)
                
                subImgsDir="%s/subImgs"%(dDirs)
                preViewDir="%s/preview"%(dDirs)
                diffResiDir="%s/diffResi"%(dDirs)
                
                if not os.path.exists(subImgsDir):
                    os.system("mkdir -p %s"%(subImgsDir))
                if not os.path.exists(preViewDir):
                    os.system("mkdir -p %s"%(preViewDir))
                if not os.path.exists(diffResiDir):
                    os.system("mkdir -p %s"%(diffResiDir))
                    
                self.log.info(sDirs)
                #G021_mon_objt_190412T11473163_2_c_c_c_c_c.fit 
                self.batchDiff(sDirs, dDirs, pattern='_2_c.fit')
                self.batchDiff(sDirs, dDirs, pattern='_2_c_c.fit')
                self.batchDiff(sDirs, dDirs, pattern='_2_c_c_c.fit')
                self.batchDiff(sDirs, dDirs, pattern='_2_c_c_c_c.fit')
                self.batchDiff(sDirs, dDirs, pattern='_2_c_c_c_c_c.fit')
                
                self.batchDiff(sDirs, dDirs, pattern='_2_c.fit', reverse=True)
                self.batchDiff(sDirs, dDirs, pattern='_2_c_c.fit', reverse=True)
                self.batchDiff(sDirs, dDirs, pattern='_2_c_c_c.fit', reverse=True)
                self.batchDiff(sDirs, dDirs, pattern='_2_c_c_c_c.fit', reverse=True)
                self.batchDiff(sDirs, dDirs, pattern='_2_c_c_c_c_c.fit', reverse=True)
                #break
            
        except Exception as e:
            print(str(e))
            tstr = traceback.format_exc()
            print(tstr)

        
def run1():
    
    #toolPath = os.getcwd()
    toolPath = '/home/gwac/img_diff_xy/image_diff'
    tools = AstroTools(toolPath)
    
    dateStr='20190412'
    camName='G031'
    curSkyId='123'
    
    srcPath00='/data/gwac_diff_xy/combine/%s'%(dateStr)
    dataDest0 = "/data/gwac_diff_xy/combineRst/%s"%(dateStr)
    if not os.path.exists(dataDest0):
        os.system("mkdir -p %s"%(dataDest0))
        
    tsim = BatchImageSim(srcPath00, dataDest0, tools, camName, curSkyId)
    
    tsim.log.info("\n\n***************\nstart diff simCombine image..\n")
    tsim.process(srcPath00, dataDest0)
    
    
#nohup /home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py > nohup.log&
#/home/gwac/img_diff_xy/anaconda3/envs/imgdiff3/bin/python OTSimulation.py
if __name__ == "__main__":
    
    run1()
    