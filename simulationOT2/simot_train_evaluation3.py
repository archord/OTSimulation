# -*- coding: utf-8 -*-
#12像素，FOT吴朝图像，TOT小辛图像，原始图像和3次旋转图像
from astropy.io import fits
import numpy as np
import math
import os
import shutil
from datetime import datetime
import matplotlib.pyplot as plt
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Convolution2D, MaxPooling2D, ZeroPadding2D

from DataPreprocess import *

#%matplotlib inline

def createModel():
    
    keras.backend.set_image_dim_ordering('th')
    model = Sequential ()
    model.add(ZeroPadding2D((1, 1), input_shape = (3, 12, 12)))
    model.add(Convolution2D(24, 3, 3))
    model.add(Activation('relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(24, 3, 3))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size =(2, 2)))
    
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(32, 3, 3))
    model.add(Activation('relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(32, 3, 3))
    model.add(Activation('relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(32, 3, 3))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size =(2, 2)))
    
    model.add(Flatten())
    model.add(Dense(32))
    model.add(Activation('relu'))
    model.add(Dense(32))
    model.add(Activation('relu'))
    model.add(Dense(2))
    model.add(Activation('softmax'))
        
    return model

def train():
    
    tpath1 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0924"
    tpath2 = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2"
    tpath3 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0927"
    
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    #X,Y,s2n = getData(tpath1, tpath3, workPath)
    timgbinPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_20180928/SIM_IMG_ALL_bin12.npz"
    X,Y,s2n = dataAugment(timgbinPath)
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    
    N_data = X.shape[0]
    N_train = int(N_data * 0.9)
    print("train: %d, test: %d"%(N_train, N_data-N_train))
    X_train, Y_train, s2n_train = X[:N_train], Y[:N_train], s2n[:N_train]
    X_test, Y_test, s2n_test = X[N_train:], Y[N_train:], s2n[N_train:]
    
    model = createModel()    
    #optimizer = keras.optimizers.SGD(lr=0.0001, decay=1e-6, momentum=0.9, nesterov=True)
    optimizer = keras.optimizers.Adam(lr=0.00001, beta_1=0.9, beta_2=0.999,decay=0.0)
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    
    model.fit(X_train, Y_train, batch_size=128, nb_epoch=5, validation_split=0.2)
    model.save("%s/model_128_5.h5"%(workPath))
    
def test():
    
    tpath1 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0924"
    tpath2 = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2"
    tpath3 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0927"
    
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    X,Y,s2n = getData(tpath1, tpath3, workPath)
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    
    N_data = X.shape[0]
    N_train = int(N_data * 0.9)
    print("train: %d, test: %d"%(N_train, N_data-N_train))
    X_train, Y_train, s2n_train = X[:N_train], Y[:N_train], s2n[:N_train]
    X_test, Y_test, s2n_test = X[N_train:], Y[N_train:], s2n[N_train:]
    
    from keras.models import load_model
    model = load_model("%s/model_128_5.h5"%(workPath))
    Y_pred = model.predict(X_test)
    pbb_threshold = 0.5
    pred_labels = np.array((Y_pred[:, 1] > pbb_threshold), dtype = "int")
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
    
    accuracy = (TP+TN)*1.0/(TP+FN+TN+FP)
    precision = (TP)*1.0/(TP+FP)
    recall = (TP)*1.0/(TP+FN)
    f1_score = 2.0*(precision*recall)/(precision+recall)
    print("accuracy=%f%%"%(accuracy*100))
    print("precision=%f%%"%(precision*100))
    print("recall=%f%%"%(recall*100))
    print("f1_score=%f%%"%(f1_score*100))
    
    falseImg = X_test[pred_labels != Y_test[:, 1]]
    falseLabel = Y_test[pred_labels != Y_test[:, 1]]
    falsePred = Y_pred[pred_labels != Y_test[:, 1]]
    falseS2n= s2n_test[pred_labels != Y_test[:, 1]]
    
    tnum1 = 0
    tnum2 = 0
    for i in range(falseImg.shape[0]):
        if falseLabel[i, 1]==1:
            tnum1 = tnum1 + 1
        else:
            tnum2 = tnum2 + 1
    print("total %d,  miss classified %d"%(Y_test.shape[0], falseImg.shape[0]))
    print("True classified as False %d"%(tnum1))
    print("False classified as True %d"%(tnum2))
    print("\n\n***********************")
    print("image of True classified as False")
    for i in range(falseImg.shape[0]):
        if falseLabel[i, 1]==1:
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(3, 3))
            axes.flat[0].imshow(falseImg[i][0], interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(falseImg[i][1], interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(falseImg[i][2], interpolation = "nearest", cmap='gray')
            axes.flat[2].set_title("predicted pbb = " + str(np.round(falsePred[i][1], 2)) + 
                                          ", label = " + str(falseLabel[i, 1]) + 
                                          ", s2n = " + str(falseS2n[i]))
            plt.show()
    
    print("\n\n***********************")
    print("image of False classified as True")
    for i in range(falseImg.shape[0]):
        if falseLabel[i, 1]==0:
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(3, 3))
            axes.flat[0].imshow(falseImg[i][0], interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(falseImg[i][1], interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(falseImg[i][2], interpolation = "nearest", cmap='gray')
            axes.flat[2].set_title("predicted pbb = " + str(np.round(falsePred[i][1], 2)) + 
                                          ", label = " + str(falseLabel[i, 1]) + 
                                          ", s2n = " + str(falseS2n[i]))
            plt.show()
     
    trueImg = X_test[pred_labels == Y_test[:, 1]]
    trueLabel = Y_test[pred_labels == Y_test[:, 1]]
    truePred = Y_pred[pred_labels == Y_test[:, 1]]
    trueS2n= s2n_test[pred_labels == Y_test[:, 1]]
    
    showNum=50
    tnum = 0
    print("\n\n***********************")
    print("image of True classified as True")
    for i in range(trueImg.shape[0]):
        if trueLabel[i, 1]==1:
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(3, 3))
            axes.flat[0].imshow(trueImg[i][0], interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(trueImg[i][1], interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(trueImg[i][2], interpolation = "nearest", cmap='gray')
            axes.flat[2].set_title("predicted pbb = " + str(np.round(truePred[i][1], 2)) + 
                                          ", label = " + str(trueLabel[i, 1]) + 
                                          ", s2n = " + str(trueS2n[i]))
            plt.show()
            tnum = tnum + 1
            if tnum>showNum:
                break
    
    tnum = 0
    print("\n\n***********************")
    print("image of False classified as False")
    for i in range(trueImg.shape[0]):
        if trueLabel[i, 1]==0:
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(3, 3))
            axes.flat[0].imshow(trueImg[i][0], interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(trueImg[i][1], interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(trueImg[i][2], interpolation = "nearest", cmap='gray')
            axes.flat[2].set_title("predicted pbb = " + str(np.round(truePred[i][1], 2)) + 
                                          ", label = " + str(trueLabel[i, 1]) + 
                                          ", s2n = " + str(trueS2n[i]))
            plt.show()
            tnum = tnum + 1
            if tnum>showNum:
                break

    
def realDataTest():
        
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_20180927"
    X, ot2prop = getRealData(realDataPath)
    ot2list = ot2prop
    
    print(X.shape)
    from keras.models import load_model
    model = load_model("%s/model_128_5.h5"%(workPath))
    preY = model.predict(X, batch_size=128)

    trueThred = 0.5
    print("minor planet classify")
    tNum = 0
    tNum2 = 0
    badNum = 0
    for i in range(ot2list.shape[0]):
        tot2 = ot2list[i]
        tlabel = tot2[4]
        ttype = tot2[5]
        if ttype=='2':
            fig, axes = plt.subplots(1, 3, figsize=(3, 1))
            axes.flat[0].imshow(X[i][0], cmap='gray')
            axes.flat[1].imshow(X[i][1], cmap='gray')
            axes.flat[2].imshow(X[i][2], cmap='gray')
            axes.flat[1].set_title("%d, %s, look=%s, type=%s, pbb=%.2f"%(i, tot2[1][:14], tlabel, ttype, preY[i][1]))
            plt.show()
            tNum = tNum + 1
            if preY[i][1]>trueThred:
                tNum2 = tNum2 + 1
                
    print("total minor planet %d, classify as true %d, with %d in badImg"%(tNum, tNum2, badNum))
    print("look back TOT classify as true")
    tNum = 0
    tNum2 = 0
    badNum = 0
    for i in range(ot2list.shape[0]):
        tot2 = ot2list[i]
        tlabel = tot2[4]
        ttype = tot2[5]
        if tlabel=='1':
            tNum = tNum + 1
            if preY[i][1]>=trueThred:
                fig, axes = plt.subplots(1, 3, figsize=(3, 1))
                axes.flat[0].imshow(X[i][0], cmap='gray')
                axes.flat[1].imshow(X[i][1], cmap='gray')
                axes.flat[2].imshow(X[i][2], cmap='gray')
                axes.flat[1].set_title("%d, %s, look=%s, type=%s, pbb=%.2f"%(i, tot2[1][:14], tlabel, ttype, preY[i][1]))
                plt.show()
                tNum2 = tNum2 + 1
    
    print("look back TOT %d, classify as true:  %d, with %d in badImg"%(tNum, tNum2, badNum))

    print("look back TOT classify as false")
    tNum = 0
    tNum2 = 0
    badNum = 0
    for i in range(ot2list.shape[0]):
        tot2 = ot2list[i]
        tlabel = tot2[4]
        ttype = tot2[5]
        if tlabel=='1':
            tNum = tNum + 1
            if preY[i][1]<trueThred:
                tNum2 = tNum2 + 1
                fig, axes = plt.subplots(1, 3, figsize=(3, 1))
                axes.flat[0].imshow(X[i][0], cmap='gray')
                axes.flat[1].imshow(X[i][1], cmap='gray')
                axes.flat[2].imshow(X[i][2], cmap='gray')
                axes.flat[1].set_title("%d, %s, look=%s, type=%s, pbb=%.2f"%(i, tot2[1][:14], tlabel, ttype, preY[i][1]))
                plt.show()
    
    print("look back TOT %d, classify as false:  %d, with %d in badImg"%(tNum, tNum2, badNum))
    print("look back FOT classify")
    tNum = 0
    tNum2 = 0
    badNum = 0
    for i in range(ot2list.shape[0]):
        tot2 = ot2list[i]
        tlabel = tot2[4]
        ttype = tot2[5]
        if tlabel!='1':
            tNum = tNum + 1
            if preY[i][1]>trueThred:
                tNum2 = tNum2 + 1
                if tNum2<40:
                    fig, axes = plt.subplots(1, 3, figsize=(3, 1))
                    axes.flat[0].imshow(X[i][0], cmap='gray')
                    axes.flat[1].imshow(X[i][1], cmap='gray')
                    axes.flat[2].imshow(X[i][2], cmap='gray')
                    axes.flat[1].set_title("%d, %s, look=%s, type=%s, pbb=%.2f"%(i, tot2[1][:14], tlabel, ttype, preY[i][1]))
                    plt.show()
    
    print("look back FOT %d, classify as true:  %d, with %d in badImg"%(tNum, tNum2, badNum))

def realDataTestAndStore():
        
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    from keras.models import load_model
    model = load_model("%s/model_128_5.h5"%(workPath))
    
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2_apart"
    tdirs = os.listdir(realDataPath)
    tdirs.sort()
    
    showNum = 50
    trueThred = 0.5
    for i, fname in enumerate(tdirs):
        if fname[:3]=='fot' and fname[-6:]=='12.npz':
            tpath21 = "%s/%s"%(realDataPath, fname)
            print(tpath21)
            tdata1 = np.load(tpath21)
            timgs = tdata1['imgs']
            tprops = tdata1['props']
        
            X = timgs
            preY = model.predict(X, batch_size=4096)
            
            falseIdx = preY[:,1]>trueThred
            falseImgs = timgs[falseIdx]
            falseProps = tprops[falseIdx]
            falsePreY = preY[falseIdx]
            
            print("total false ot %d, classify as true %d, %f%%"%(X.shape[0], falseImgs.shape[0], falseImgs.shape[0]*100.0/X.shape[0]))
            
            dpath21 = '%s/%s_F2T.npz'%(realDataPath, fname[:-4])
            np.savez_compressed(dpath21, imgs=falseImgs, props=falseProps)
            print("save %d False classify as True bin to %s"%(falseImgs.shape[0], dpath21))
            
            '''
            X = falseImgs
            for i in range(X.shape[0]):
                tot2 = falseProps[i]
                tlabel = tot2[4]
                ttype = tot2[5]
                
                fig, axes = plt.subplots(1, 3, figsize=(3, 1))
                axes.flat[0].imshow(X[i][0], cmap='gray')
                axes.flat[1].imshow(X[i][1], cmap='gray')
                axes.flat[2].imshow(X[i][2], cmap='gray')
                axes.flat[1].set_title("%d, %s, look=%s, type=%s, pbb=%.2f"%(i, tot2[1][:14], tlabel, ttype, falsePreY[i][1]))
                plt.show()
                if i>showNum:
                    break
            '''    
            #break
    
if __name__ == "__main__":
    
    train()



