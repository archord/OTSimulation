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
                "#  14 RA                     Fixed aperture magnitude vector                            [deg]  \n"\
                "#  15 DEC                    RMS error vector for fixed aperture mag.                   [deg]  \n"\
                "#  16 probability            machine learning predict probability.                             \n"\
                "#  17 OT FLAG                1: resi not match temp; 0:resi match temp.                       \n"\
                "#  18 stamp image name       the concatenate of 3 stamp image from obj, temp, resi.           \n"\
                "#  19 dateUtc                    RMS error vector for fixed aperture mag.                   [deg]  \n"\
                "#  20 X_TEMP                 Object position along x                                    [pixel]\n"\
                "#  21 Y_TEMP                 Object position along y                                    [pixel]\n"
        
        self.theader2='#CH x y flux fluxErr fluxMax elongation ellipticity classstar background fwhm flags mag magerr '\
                'ra dec probability otflag stampName dateUtc xtemp ytemp\n'
        self.catFormate="%.4f,%.4f,%.2f,%.2f,%.2f,%.3f,%.3f,%.3f,%.2f,%.2f,%d,%.4f,%.4f,%f,%f,%f,%d,%s,%s,%.4f,%.4f\n"
    
    def doClassifyFile(self, tpath, fname):
    
        try:
            print("start doClassifyFile")
            rstParms = np.array([])
            obsUtc = ''
            tpath0 = "%s/%s"%(tpath, fname)
            print(tpath0)
            
            if len(fname)>0 and os.path.exists(tpath0):
                
                print("start doClassifyFile 1")
                tdata1 = np.load(tpath0)
                timgs32 = tdata1['imgs']
                parms = tdata1['parms']
                obsUtc = tdata1['obsUtc']
                print(timgs32.shape)
                
                #fs2n = 1.087/props[:,12].astype(np.float)
                
                if timgs32.shape[0]>0:
                    timgs = getImgStamp(timgs32, size=self.imgSize, padding = 1, transMethod='none')
                    print(timgs.shape)
                    preY = self.model.predict(timgs, batch_size=128)
                    #model = load_model(self.modelPath,custom_objects={'concatenate':keras.layers.concatenate})
                    #preY = model.predict(timgs, batch_size=128)
                    print(preY.shape)
                    
                    predProbs = preY[:, 1]
                    predProbs = predProbs.reshape([predProbs.shape[0],1])
                    rstParms = np.concatenate((parms, predProbs), axis=1)
                    self.log.info("total %d subImgs, %d is valid and classified"%(timgs32.shape[0],timgs.shape[0]))
            
            print("end doClassifyFile")
        except Exception as e:
            tstr = traceback.format_exc()
            print("doClassifyFile")
            print(tstr)
            self.log.error(tstr)
            
        return rstParms, obsUtc
        
    def doClassifyAndUpload(self, subImgPath, totFile, fotFile, 
                          fullImgPath, newImg, tmpImg, resImg, origName, serverIP, 
                          prob=0.01, maxNEllip=0.6, maxMEllip=0.5, reverse=False):

        self.log.info("start new thread classifyAndUpload %s"%(origName))   
        print("start new thread classifyAndUpload %s"%(origName))
        
        starttime = datetime.now()
        self.pbb_threshold = prob
        try:
            nameBase = origName[:origName.index(".")]
            
            dateStr = nameBase.split('_')[3][:6]
            camName = nameBase[:4]
            cmbNum = 5
            #tidx = nameBase.index('_c')+2
            #cmbNum = nameBase[tidx:tidx+3] #'G021_tom_objt_190109T13531492_c005.fit'
            crossTaskName = "%s_%s_c%03d"%(dateStr, camName, cmbNum)
            self.log.info("crossTaskName %s"%(crossTaskName))   
            print("crossTaskName %s"%(crossTaskName))
            
            tParms1, obsUtc1 = self.doClassifyFile(subImgPath, totFile)
            print("doClassifyAndUpload 001")
            if tParms1.shape[0]>0:
                tParms1 = tParms1[tParms1[:,6]<maxNEllip]
                #tParms1 = tParms1[(tParms1[:,6]<maxMEllip) & (tParms1[:,15]>=prob)]
                if tParms1.shape[0]>0:
                    tflags1 = np.ones((tParms1.shape[0],1)) #OT FLAG 
                    tParms1 = np.concatenate((tParms1, tflags1), axis=1)
            
            print("doClassifyAndUpload 002")
            tParms2, obsUtc2 = self.doClassifyFile(subImgPath, fotFile)
            if tParms2.shape[0]>0:
                tParms2 = tParms2[(tParms2[:,6]<maxMEllip) & (tParms2[:,15]>=prob)]
                if tParms2.shape[0]>0:
                    tflags2 = np.zeros((tParms2.shape[0],1)) #OT FLAG 
                    tParms2 = np.concatenate((tParms2, tflags2), axis=1)
            
            print("doClassifyAndUpload 003")
            if tParms1.shape[0]>0 and tParms2.shape[0]>0 and tParms2.shape[0]<50:
                tParms = np.concatenate((tParms1, tParms2), axis=0)
            elif tParms1.shape[0]>0:
                tParms = tParms1
            elif tParms2.shape[0]>0 and tParms2.shape[0]<25:
                tParms = tParms2
            else:
                tParms = np.array([])
                
            print("doClassifyAndUpload 004")
            if tParms.shape[0]==0:
                print("doClassifyAndUpload 005")
                self.log.info("after classified, no OT candidate left")
            elif tParms.shape[0]>0:
                print("doClassifyAndUpload 006")
                tSubImgs, tParms = getWindowImgs(fullImgPath, newImg, tmpImg, resImg, tParms, 100)
                if tParms.shape[0]>0:
                    self.log.info("after classified, %s total get %d sub images"%(origName, tSubImgs.shape[0]))
                    print("after classified, %s total get %d sub images"%(origName, tSubImgs.shape[0]))
                    
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
                        
                        tImgName = "%s_%05d.jpg"%(nameBase,i)
                        timgNames.append(tImgName)
                        savePath = "%s/%s"%(fullImgPath, tImgName)
                        Image.fromarray(sub2Con).save(savePath)
                        i = i+1
            
                    catName = tImgName = "%s.cat"%(nameBase)
                    catPath = "%s/%s"%(fullImgPath, catName)
                    fp0 = open(catPath, 'w')
                    fp0.write(self.theader2)
                    i=0
                    for td in tParms:
                        tstr = self.catFormate%\
                            (td[0],td[1],td[2],td[3],td[4],td[5],td[6],td[7],td[8],td[9],td[10],td[11],td[12],td[13],
                             td[14],td[15],td[16], timgNames[i], obsUtc1, td[0],td[1])
                        fp0.write(tstr)
                        i=i+1
                    fp0.close()
                    
                    self.doUpload(fullImgPath,[catName],'crossOTList',serverIP, crossTaskName)
                    self.doUpload(fullImgPath,timgNames,'crossOTStamp',serverIP, crossTaskName)
                    
            if tParms2.shape[0]>=50:
                self.log.error("too more matched OT candidate, skip upload matched to db: after classified, %s total get %d matchend sub images"%(origName, tParms2.shape[0]))
            os.system("rm -rf %s"%(fullImgPath))
        
        except Exception as e:
            self.log.error('classifyAndUpload error')
            self.log.error(str(e))
            tstr = traceback.format_exc()
            self.log.error(tstr)
        endtime = datetime.now()
        runTime = (endtime - starttime).seconds
        self.log.info("********** classifyAndUpload %s use %d seconds"%(origName, runTime))
        
    
    def crossTaskCreate(self, taskName, crossMethod, dateStr, cofParms, serverIP):
        
        try:
            self.log.info("crossTaskCreate %s"%(taskName))
            turl = "%s/gwebend/crossTaskCreate.action"%(serverIP)
            
            cofParms['taskName'] = taskName
            cofParms['crossMethod'] = crossMethod
            cofParms['dateStr'] = dateStr
            
            self.log.debug(cofParms)
            #print(values)
            #print(files)
            msgSession = requests.Session()
            r = msgSession.post(turl, data=cofParms)
            
            self.log.info(r.text)
        except Exception as e:
            tstr = traceback.format_exc()
            self.log.error(tstr)
            
    
    def doUpload(self, path, fnames, ftype, serverIP, taskName):
        
        try:
            turl = "%s/gwebend/crossTaskUpload.action"%(serverIP)
            
            sendTime = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
            values = {'taskName': taskName, 'fileType': ftype, 'sendTime': sendTime}
            files = []
            
            for tfname in fnames:
                tpath = "%s/%s"%(path, tfname)
                files.append(('fileUpload', (tfname,  open(tpath,'rb'), 'text/plain')))
            
            print(values)
            #print(files)
            msgSession = requests.Session()
            r = msgSession.post(turl, files=files, data=values)
            
            self.log.info(r.text)
        except Exception as e:
            tstr = traceback.format_exc()
            self.log.error(tstr)
            
            