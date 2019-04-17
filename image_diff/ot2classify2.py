import numpy as np
import os
import cv2
import requests
import traceback
from datetime import datetime
import scipy.ndimage
from PIL import Image
import keras
from keras.models import load_model
from DataPreprocess import getImgStamp
from gwac_util import zscale_image, getWindowImgs

class OT2Classify(object):
    
    def __init__(self, dataRoot, log, modelName='model_128_5_RealFOT_8_190111.h5'): 
        
        self.dataRoot=dataRoot
        self.modelName=modelName
        self.modelName3='model_80w_20190403_branch3_train12_79.h5'
        self.modelPath="%s/tools/mlmodel/%s"%(dataRoot,self.modelName3)
        
        self.imgSize = 64
        self.pbb_threshold = 0.5
        self.model = load_model(self.modelPath,custom_objects={'concatenate':keras.layers.concatenate})
        self.log = log
        
        self.theader="#   1 X_IMAGE                Object position along x                                    [pixel]\n"\
                "#   2 Y_IMAGE                Object position along y                                    [pixel]\n"\
                "#   3 FLUX_APER              Flux vector within fixed circular aperture(s)              [count]\n"\
                "#   4 FLUXERR_APER           RMS error vector for aperture flux(es)                     [count]\n"\
                "#   5 FLUX_MAX               Peak flux above background                                 [count]\n"\
                "#   6 ELONGATION             A_IMAGE/B_IMAGE                                                   \n"\
                "#   7 ELLIPTICITY            1 - B_IMAGE/A_IMAGE                                               \n"\
                "#   8 CLASS_STAR             S/G classifier output                                             \n"\
                "#   9 BACKGROUND             Background at centroid position                            [count]\n"\
                "#  10 FWHM_IMAGE             FWHM assuming a gaussian core                              [pixel]\n"\
                "#  11 FLAGS                  Extraction flags                                                  \n"\
                "#  12 MAG_APER               Fixed aperture magnitude vector                            [mag]  \n"\
                "#  13 MAGERR_APER            RMS error vector for fixed aperture mag.                   [mag]  \n"\
                "#  14 X_TEMP                 Object position along x                                    [pixel]\n"\
                "#  15 Y_TEMP                 Object position along y                                    [pixel]\n"\
                "#  16 RA                     Fixed aperture magnitude vector                            [deg]  \n"\
                "#  17 DEC                    RMS error vector for fixed aperture mag.                   [deg]  \n"\
                "#  18 probability            machine learning predict probability.                             \n"\
                "#  19 OT FLAG                1: resi not match temp; 0:resi match temp.                       \n"\
                "#  20 stamp image name       the concatenate of 3 stamp image from obj, temp, resi.           \n"
            
        self.catFormate="%.4f,%.4f,%.2f,%.2f,%.2f,%.3f,%.3f,%.3f,%.2f,%.2f,%d,%.4f,%.4f,%f,%f,%.3f,%d,%s\n"
    
    def doClassifyFile(self, tpath, fname):
    
        rstParms = np.array([])
        tpath0 = "%s/%s"%(tpath, fname)
        if len(fname)>0 and os.path.exists(tpath0):
                
            tdata1 = np.load(tpath0)
            timgs32 = tdata1['imgs']
            parms = tdata1['parms']
            #fs2n = 1.087/props[:,12].astype(np.float)
            
            if timgs32.shape[0]>0:
                timgs = getImgStamp(timgs32, size=self.imgSize, padding = 1, transMethod='none')
                preY = self.model.predict(timgs, batch_size=128)
                
                predProbs = preY[:, 1]
                predProbs = predProbs.reshape([predProbs.shape[0],1])
                rstParms = np.concatenate((parms, predProbs), axis=1)
                self.log.info("total %d subImgs, %d is valid and classified"%(timgs32.shape[0],timgs.shape[0]))
        
        return rstParms
    
    def doUpload(self, path, fnames, ftype, serverIP):
        
        try:
            turl = "%s/gwebend/commonFileUpload.action"%(serverIP)
            
            sendTime = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
            values = {'fileType': ftype, 'sendTime': sendTime}
            files = []
            
            for tfname in fnames:
                tpath = "%s/%s"%(path, tfname)
                files.append(('fileUpload', (tfname,  open(tpath,'rb'), 'text/plain')))
            
            #print(values)
            #print(files)
            msgSession = requests.Session()
            r = msgSession.post(turl, files=files, data=values)
            
            self.log.info(r.text)
        except Exception as e:
            tstr = traceback.format_exc()
            self.log.error(tstr)
        
    def doClassifyAndUpload(self, subImgPath, totFile, fotFile, 
                          fullImgPath, newImg, tmpImg, resImg, origName, serverIP, 
                          prob=0.01, maxNEllip=0.6, maxMEllip=0.5, reverse=False):

        self.log.debug("start new thread classifyAndUpload %s"%(origName))        
        
        starttime = datetime.now()
        self.pbb_threshold = prob
        try:
            nameBase = origName[:origName.index(".")]
            
            tParms1 = self.doClassifyFile(subImgPath, totFile)
            if tParms1.shape[0]>0:
                #tParms1 = tParms1[(tParms1[:,6]<maxMEllip) & (tParms1[:,17]>=prob)]
                tParms1 = tParms1[tParms1[:,17]>=prob]
                self.log.info("after classified, %s is true"%(tParms1.shape[0]))
                if tParms1.shape[0]>0:
                    tflags1 = np.ones((tParms1.shape[0],1)) #OT FLAG 
                    tParms1 = np.concatenate((tParms1, tflags1), axis=1)
            
            tParms = tParms1
                
            if tParms.shape[0]>0:
                tSubImgs, tParms = getWindowImgs(fullImgPath, newImg, tmpImg, resImg, tParms, 100)
                if tParms.shape[0]>0:
                    self.log.info("after classified, %s total get %d sub images"%(origName, tSubImgs.shape[0]))
                    
                    i=1
                    timgNames = []
                    for timg in tSubImgs:
                        objWid, tmpWid, resiWid = timg[0],timg[1],timg[2]
                        
                        objWidz = zscale_image(objWid)
                        tmpWidz = zscale_image(tmpWid)
                        resiWidz = zscale_image(resiWid)
                        objWidz = scipy.ndimage.zoom(objWidz, 2, order=0)
                        tmpWidz = scipy.ndimage.zoom(tmpWidz, 2, order=0)
                        resiWidz = scipy.ndimage.zoom(resiWidz, 2, order=0)
                        
                        objWidz = objWidz.reshape(objWidz.shape[0], objWidz.shape[1],1).repeat(3,2)
                        tmpWidz = tmpWidz.reshape(tmpWidz.shape[0], tmpWidz.shape[1],1).repeat(3,2)
                        resiWidz = resiWidz.reshape(resiWidz.shape[0], resiWidz.shape[1],1).repeat(3,2)
                        
                        shift00=3
                        cv2.circle(objWidz, (int(objWidz.shape[0]/2)-shift00, int(objWidz.shape[1]/2)-shift00), 10, (0,255,0), thickness=2)
                        cv2.circle(tmpWidz, (int(tmpWidz.shape[0]/2)-shift00, int(tmpWidz.shape[1]/2)-shift00), 10, (0,255,0), thickness=2)
                        cv2.circle(resiWidz, (int(resiWidz.shape[0]/2)-shift00, int(resiWidz.shape[1]/2)-shift00), 10, (0,255,0), thickness=2)
                        
                        spaceLine = np.ones((objWidz.shape[0],5), dtype=np.uint8)*255
                        spaceLine = spaceLine.reshape(spaceLine.shape[0], spaceLine.shape[1],1).repeat(3,2)
                        sub2Con = np.concatenate((objWidz, spaceLine, tmpWidz, spaceLine, resiWidz), axis=1)
                        
                        if reverse:
                            tImgName = "%s_%05d_r.jpg"%(nameBase,i)
                        else:
                            tImgName = "%s_%05d.jpg"%(nameBase,i)
                        timgNames.append(tImgName)
                        savePath = "%s/%s"%(fullImgPath, tImgName)
                        Image.fromarray(sub2Con).save(savePath)
                        i = i+1
            
                    catName = "%s.cat"%(nameBase)
                    catPath = "%s/%s"%(fullImgPath, catName)
                    fp0 = open(catPath, 'w')
                    #fp0.write(self.theader)
                    i=0
                    for td in tParms:
                        tstr = "%.4f,%.4f,%.2f,%.2f,%.2f,%.3f,%.3f,%.3f,%.2f,%.2f,%d,%.4f,%.4f,%.4f,%.4f,%f,%f,%.3f,%d,%s\n"%\
                            (td[0],td[1],td[2],td[3],td[4],td[5],td[6],td[7],td[8],td[9],td[10],td[11],td[12],td[13],
                             td[14],td[15],td[16],td[17],td[18], timgNames[i])
                        fp0.write(tstr)
                        i=i+1
                    fp0.close()
                    
                    self.doUpload(fullImgPath,[catName],'cmbot1',serverIP)
                    self.doUpload(fullImgPath,timgNames,'cmbot1img',serverIP)
                    
            if tParms.shape[0]==0:
                self.log.info("total %d resiObj, after classified, no OT candidate left"%(tParms1.shape[0]))
            os.system("rm -rf %s"%(fullImgPath))
        
        except Exception as e:
            self.log.error('classifyAndUpload error')
            self.log.error(str(e))
            tstr = traceback.format_exc()
            self.log.error(tstr)
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** classifyAndUpload %s use %d seconds"%(origName, runTime))
        