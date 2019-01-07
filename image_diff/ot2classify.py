import numpy as np
import os
import cv2
import scipy.ndimage
from PIL import Image
from keras.models import load_model
from DataPreprocess import getImgStamp
from gwac_util import zscale_image

class OT2Classify(object):
    
    def __init__(self, dataRoot, modelName='model_128_5_RealFOT_8.h5'): 
        
        self.dataRoot=dataRoot
        self.modelName=modelName
        self.modelPath="%s/tools/mlmodel/%s"%(dataRoot,self.modelName)
        
        self.imgSize = 8
        self.pbb_threshold = 0.5
        self.model = load_model(self.modelPath)
        
        self.theader="#   1 X_IMAGE                Object position along x                                    [pixel]"\
                "#   2 Y_IMAGE                Object position along y                                    [pixel]"\
                "#   3 FLUX_APER              Flux vector within fixed circular aperture(s)              [count]"\
                "#   4 FLUXERR_APER           RMS error vector for aperture flux(es)                     [count]"\
                "#   5 FLUX_MAX               Peak flux above background                                 [count]"\
                "#   6 ELONGATION             A_IMAGE/B_IMAGE                                                   "\
                "#   7 ELLIPTICITY            1 - B_IMAGE/A_IMAGE                                               "\
                "#   8 CLASS_STAR             S/G classifier output                                             "\
                "#   9 BACKGROUND             Background at centroid position                            [count]"\
                "#  10 FWHM_IMAGE             FWHM assuming a gaussian core                              [pixel]"\
                "#  11 FLAGS                  Extraction flags                                                  "\
                "#  12 MAG_APER               Fixed aperture magnitude vector                            [mag]  "\
                "#  13 MAGERR_APER            RMS error vector for fixed aperture mag.                   [mag]  "\
                "#  14 RA                     Fixed aperture magnitude vector                            [deg]  "\
                "#  15 DEC                    RMS error vector for fixed aperture mag.                   [deg]  "\
                "#  16 probability            machine learning predict probability.                             "\
                "#  17 OT FLAG                1: resi not match temp; 0:resi match temp.                       "\
                "#  18 stamp image name       the concatenate of 3 stamp image from obj, temp, resi.           "
            
        self.catFormate="%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%.3f,%.3f,%.2f,%.2f,%d,%.4f,%.4f,%f,%f,%.3f,%d,%s\n"
    
    def doClassifyFile(self, tpath, fname):
    
        rstParms = np.array([])
        tpath = "%s/%s"%(tpath, fname)
        if os.path.exists(tpath):
                
            tdata1 = np.load(tpath)
            timgs32 = tdata1['imgs']
            parms = tdata1['parms']
            #fs2n = 1.087/props[:,12].astype(np.float)
            
            if timgs32.shape[0]>0:
                timgs = getImgStamp(timgs32, size=self.imgSize, padding = 0, transMethod='none')
                preY = self.model.predict(timgs, batch_size=128)
                predProbs = preY[:, 1]
                rstParms = np.concatenate((parms, predProbs), axis=1)
        
        return rstParms
        
        
    def classifyAndUpload(self, subImgPath, totFile, fotFile, fullImgPath, newImg, tmpImg, resImg, origName, prob=0.01):
        
        nameBase = origName[:origName.index(".")]
        
        tParms1 = self.doClassifyFile(subImgPath, totFile)
        tParms2 = self.doClassifyFile(subImgPath, fotFile)
        tflags1 = np.ones((tParms1.shape[0],1)) #OT FLAG 
        tflags2 = np.zeros((tParms2.shape[0],1)) #OT FLAG 
        tParms1 = np.concatenate((tParms1, tflags1), axis=1)
        tParms2 = np.concatenate((tParms2, tflags2), axis=1)
        tParms = np.concatenate((tParms1, tParms2), axis=0)
        
        tParms = tParms[tParms[:,-1]>=prob]
        tSubImgs, tParms = self.tools.getWindowImgs(fullImgPath, newImg, tmpImg, resImg, tParms, 100)
        
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
            
            cv2.circle(objWidz, (int(objWidz.shape[0]/2), int(objWidz.shape[1]/2)), 10, (0,255,0), thickness=1)
            cv2.circle(tmpWidz, (int(tmpWidz.shape[0]/2), int(tmpWidz.shape[1]/2)), 10, (0,255,0), thickness=1)
            cv2.circle(resiWidz, (int(resiWidz.shape[0]/2), int(resiWidz.shape[1]/2)), 10, (0,255,0), thickness=1)
            
            spaceLine = np.ones((objWidz.shape[0],5))*255
            spaceLine = spaceLine.reshape(spaceLine.shape[0], spaceLine.shape[1],1).repeat(3,2)
            sub2Con = np.concatenate((objWidz, spaceLine, tmpWidz, spaceLine, resiWidz), axis=1)
            
            tImgName = "%s_%05d.jpg"%(nameBase,i)
            timgNames.append(tImgName)
            savePath = "%s/%s"%(fullImgPath, tImgName)
            Image.fromarray(sub2Con).save(savePath)

        catName = tImgName = "%s_%05d.cat"%(nameBase,tParms.shape[0])
        catPath = "%s/%s"%(fullImgPath, catName)
        tParms = np.concatenate((tParms, np.array(timgNames)), axis=1)
        fp0 = open(catPath, 'w')
        fp0.write(self.theader)
        for td in tParms:
            tstr = ",".join(td) + '\n'
            fp0.write(tstr)
        fp0.close()