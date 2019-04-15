# -*- coding: utf-8 -*-
import numpy as np
import math
import os
import shutil
from datetime import datetime
import keras
from keras.models import Sequential, Model
from keras.layers import Dense, Dropout, Activation, Flatten, Input
from keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D, Concatenate, Cropping2D, Lambda, concatenate
from keras import backend as K
import traceback
from keras.models import load_model
from gwac_util import zscale_image
import matplotlib.pyplot as plt

                
def doAll():
    
    #dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    dateStr = '20190403'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    tModelNamePart = "80w_%s_dropout_train10"%(dateStr) #944376
    
    destName = 'refine1'
    buildMisMatchSample2(workPath, destName, tModelNamePart)
    '''
    for i in range(1,10):
        imgsFile = 'train%d'%(i)
        #outMisMatch(workPath, imgsFile, destName, tModelNamePart)
        correctMisMatch(workPath, imgsFile, destName, tModelNamePart)
        #break
    '''
   
def outMisMatch(workPath, imgsFile, destName, tModelNamePart):
    
    dataPath = "%s/data"%(workPath)
    tpath = "%s/%s.npz"%(dataPath, imgsFile)
    print(tpath)
    
    destPath = "%s/%s/%s"%(dataPath, destName, imgsFile)
    if not os.path.exists(destPath):
        os.system("mkdir -p %s"%(destPath))
    destPath0 = "%s/0"%(destPath)
    if not os.path.exists(destPath0):
        os.system("mkdir %s"%(destPath0))
    destPath1 = "%s/1"%(destPath)
    if not os.path.exists(destPath1):
        os.system("mkdir %s"%(destPath1))
        
    tdata = np.load(tpath)
    X_test = tdata['X']
    Y_test = tdata['Y']
    s2n_test = tdata['s2n']
    print(X_test.shape)
    print(Y_test.shape)
    print(s2n_test.shape)
    
    K.set_image_data_format('channels_first')
    modelName = "model_80w_20190403_dropout_train11_09.h5"
    model = load_model("%s/%s"%(workPath, modelName))
    Y_pred = model.predict(X_test)
    pbb_threshold = 0.5
    pred_labels = np.array((Y_pred[:, 1] >= pbb_threshold), dtype = "int")
    print("Correctly classified %d out of %d"%((pred_labels == Y_test[:, 1].astype(int)).sum(), Y_test.shape[0]))
    print("accuracy = %f"%(1.*(pred_labels == Y_test[:, 1].astype(int)).sum() / Y_test.shape[0]))

    TIdx = Y_test[:, 1]==1
    FIdx = Y_test[:, 1]==0
    T_pred_rst = pred_labels[TIdx]
    F_pred_rst = pred_labels[FIdx]
    print(T_pred_rst.shape)
    print(F_pred_rst.shape)
    
    TP = ((T_pred_rst == 1).astype(int)).sum()
    TN = ((F_pred_rst == 0).astype(int)).sum()
    FP = ((F_pred_rst == 1).astype(int)).sum()
    FN = ((T_pred_rst == 0).astype(int)).sum()
    print("total=%d,TP=%d,TN=%d,FP=%d,FN=%d"%(Y_test.shape[0],TP, TN, FP, FN))
    
    for i in range(X_test.shape[0]):
        try:
            ty = Y_test[i][1]
            if ty!=pred_labels[i]:
                
                objWidz = zscale_image(X_test[i][0])
                tmpWidz = zscale_image(X_test[i][1])
                resiWidz = zscale_image(X_test[i][2])
                if objWidz.shape[0] == 0:
                    objWidz = X_test[i][0]
                if tmpWidz.shape[0] == 0:
                    tmpWidz = X_test[i][1]
                if resiWidz.shape[0] == 0:
                    resiWidz = X_test[i][2]
                plt.clf()
                fig, axes = plt.subplots(1, 3, figsize=(6, 2))
                axes.flat[0].imshow(objWidz, interpolation = "nearest", cmap='gray')
                axes.flat[1].imshow(tmpWidz, interpolation = "nearest", cmap='gray')
                axes.flat[2].imshow(resiWidz, interpolation = "nearest", cmap='gray')
                axes.flat[1].set_title("pbb = " + str(np.round(Y_pred[i][1], 2)) + 
                                              ", label = " + str(Y_pred[i, 1]) + 
                                              ", s2n = " + str(s2n_test[i]))
                
                #plt.show()
                savePath = "%s/%d/%06d.jpg"%(destPath, ty, i)
                plt.savefig(savePath, bbox_inches='tight') 
                #break
        except Exception as e:
            tstr = traceback.format_exc()
            print(tstr)
    
def correctMisMatch(workPath, imgsFile, destName, tModelNamePart):
    
    dataPath = "%s/data"%(workPath)
    tpath = "%s/%s.npz"%(dataPath, imgsFile)
    print(tpath)
            
    tdata = np.load(tpath)
    Y = tdata['Y']
    print(Y.shape)
    
    srcPath10 = "%s/%s/orig/%s/0"%(dataPath, destName, imgsFile)
    srcPath11 = "%s/%s/orig/%s/1"%(dataPath, destName, imgsFile)
    srcPath20 = "%s/%s/correct/%s/0"%(dataPath, destName, imgsFile)
    srcPath21 = "%s/%s/correct/%s/1"%(dataPath, destName, imgsFile)
    
    imgs0 = os.listdir(srcPath10)
    imgs0.sort()
    tNum0 = 0
    for timg in imgs0:
        tIdx = int(timg[:-4])
        tpath = "%s/%s"%(srcPath20, timg)
        if os.path.exists(tpath):
            Y[tIdx][1]=1
            Y[tIdx][0]=0
            tNum0+=1
        
    imgs1 = os.listdir(srcPath11)
    imgs1.sort()
    tNum1 = 0
    for timg in imgs1:
        tIdx = int(timg[:-4])
        tpath = "%s/%s"%(srcPath21, timg)
        if not os.path.exists(tpath):
            Y[tIdx][1]=0
            Y[tIdx][0]=1
            tNum1+=1
    
    print("%s, F2T:%d,%d, T2F:%d,%d"%(imgsFile, len(imgs0), tNum0, len(imgs1), tNum1))
    tpath2 = "%s/%s_Y%s.npz"%(dataPath, imgsFile, destName)
    np.savez_compressed(tpath2, Y=Y)
    
def buildMisMatchSample(workPath, destName, tModelNamePart):
    
    tx = []
    ty = []
    ts2n = []
    tNum0 = 0
        
    for i in range(1,10):
        imgsFile = 'train%d'%(i)
        dataPath = "%s/data"%(workPath)
        tpath = "%s/%s.npz"%(dataPath, imgsFile)
        print(tpath)
                
        tdata = np.load(tpath)
        X = tdata['X']
        s2n = tdata['s2n']
        print(X.shape)
        
        tlables = [0,1]
        for tlb in tlables:
            srcPath10 = "%s/%s/orig/%s/%d"%(dataPath, destName, imgsFile, tlb)
            srcPath20 = "%s/%s/correct/%s/%d"%(dataPath, destName, imgsFile, tlb)
            imgs0 = os.listdir(srcPath10)
            imgs0.sort()
            for timg in imgs0:
                tIdx = int(timg[:-4])
                tx.append(X[tIdx])
                ts2n.append(s2n[tIdx])
                tpath = "%s/%s"%(srcPath20, timg)
                if os.path.exists(tpath):
                    ty.append((0,1))
                else:
                    ty.append((1,0))
                tNum0+=1
        
    
    print("%s, %d"%(destName, tNum0))
    tpath2 = "%s/%s_allMisMatch.npz"%(dataPath, destName)
    np.savez_compressed(tpath2, X=np.array(tx), Y=np.array(ty), s2n=np.array(ts2n))
            
def buildMisMatchSample2(workPath, destName, tModelNamePart):
    
    tx = []
    ty = []
    origy = []
    ts2n = []
    tNum0 = 0
        
    for i in range(1,10):
        imgsFile = 'train%d'%(i)
        dataPath = "%s/data"%(workPath)
        tpath = "%s/%s.npz"%(dataPath, imgsFile)
        print(tpath)
                
        tdata = np.load(tpath)
        X = tdata['X']
        s2n = tdata['s2n']
        print(X.shape)
        
        tlables = [0,1]
        for tlb in tlables:
            srcPath10 = "%s/%s/orig/%s/%d"%(dataPath, destName, imgsFile, tlb)
            srcPath20 = "%s/%s/correct/%s/%d"%(dataPath, destName, imgsFile, tlb)
            imgs0 = os.listdir(srcPath10)
            imgs0.sort()
            for timg in imgs0:
                tIdx = int(timg[:-4])
                tx.append(X[tIdx])
                ts2n.append(s2n[tIdx])
                tpath = "%s/%s"%(srcPath20, timg)
                if os.path.exists(tpath):
                    ty.append((0,1))
                else:
                    ty.append((1,0))
                origy.append(tlb)
                tNum0+=1
        
    
    print("%s, %d"%(destName, tNum0))
    tpath2 = "%s/%s_allMisMatch2.npz"%(dataPath, destName)
    np.savez_compressed(tpath2, X=np.array(tx), Y=np.array(ty), s2n=np.array(ts2n), origY=np.array(origy))
    
if __name__ == "__main__":
    
    doAll()



