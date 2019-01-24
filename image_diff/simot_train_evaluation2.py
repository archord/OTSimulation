# -*- coding: utf-8 -*-
from astropy.io import fits
import numpy as np
import math
import os
import shutil
from datetime import datetime
import matplotlib.pyplot as plt
import keras
from keras.models import Sequential, Model
from keras.layers import Dense, Dropout, Activation, Flatten, Input
from keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D, Concatenate, Cropping2D
from DataPreprocess import getData2, getRealData, saveImgs
from gwac_util import zscale_image
    
def createModel1():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=28,data_format='channels_first')(input0)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(24, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    out = Dense(64, activation='relu')(model1)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0
    
def createModel():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=28,data_format='channels_first')(input0)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(24, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    
    model2 = Conv2D(18, (5, 5), activation='relu')(input0)
    model2 = MaxPooling2D(pool_size =(3, 3))(model2)
    model2 = Conv2D(36, (4, 4), padding='same', activation='relu')(model2)
    model2 = Conv2D(36, (4, 4), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Flatten()(model2)
    
    conc = Concatenate()([model1, model2])
    out = Dense(64, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0

#train with real Sample of False miss classify as True
def train(totpath, fotpath, workPath, tSampleNamePart, tModelNamePart):
    
    X,Y,s2n = getData2(totpath, fotpath, workPath, tSampleNamePart)
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
    
    model.fit(X_train, Y_train, batch_size=128, epochs=100, validation_split=0.2)
    modelName = "model_RealFOT_%s.h5"%(tModelNamePart)
    model.save("%s/%s"%(workPath, modelName))

def doAll():
    
    fotpath = "/home/xy/Downloads/myresource/deep_data2/simot/multi_scale_20190120/all"
    totpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_20190120"
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/simot/multi_scale_20190120/20190116tot"
    
    #dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    dateStr = '20190122'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    tSampleNamePart = "64_fot10w_%s"%(dateStr)
    tModelNamePart = "64_100_fot10w_%s_dropout"%(dateStr)
    #tModelNamePart = "8_100_fot10w_%s_dropout"%(dateStr)
    train(totpath, fotpath, workPath, tSampleNamePart, tModelNamePart)
    test(totpath, fotpath, workPath, tSampleNamePart, tModelNamePart)
    
def modelCompare():
    
    fotpath = "/home/xy/Downloads/myresource/deep_data2/simot/multi_scale_20190120/all"
    totpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_20190120"
    realDataPath = "/home/xy/Downloads/myresource/deep_data2/simot/multi_scale_20190120/20190116tot"
    
    #dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    dateStr = '20190122'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    tSampleNamePart = "64_fot10w_%s"%(dateStr)
    tModelNamePart1 = "64_100_fot10w_%s_dropout"%(dateStr)
    tModelNamePart2 = "8_100_fot10w_%s_dropout"%(dateStr)
    #realDataTest(realDataPath, workPath, tSampleNamePart, tModelNamePart1, tModelNamePart2)
    realDataTest2(realDataPath, workPath, tSampleNamePart, tModelNamePart1, tModelNamePart2)
    
def realDataTest2(realOtPath, workPath, tSampleNamePart, tModelNamePart1, tModelNamePart2):
    
    X,Y,s2n = getRealData(realOtPath, workPath, tSampleNamePart)
    
    subNum = 1000
    X = X[:subNum]
    Y = Y[:subNum]
    s2n = s2n[:subNum]
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    
    X_test, Y_test, s2n_test = X, Y, s2n
    y = np.zeros(X_test.shape[0])
    Y_test = np.array([np.logical_not(y), y]).transpose()
    
    from keras.models import load_model
    
    modelName1 = "model_RealFOT_%s.h5"%(tModelNamePart1)
    model = load_model("%s/%s"%(workPath, modelName1))
    Y_pred1 = model.predict(X_test)
    
    modelName2 = "model_RealFOT_%s.h5"%(tModelNamePart2)
    model = load_model("%s/%s"%(workPath, modelName2))
    Y_pred2 = model.predict(X_test)
    
    
    pbb_threshold = 0.5
    pred_labels1 = np.array((Y_pred1[:, 1] > pbb_threshold), dtype = "int")
    pred_labels2 = np.array((Y_pred2[:, 1] > pbb_threshold), dtype = "int")
    
    model1True = pred_labels1[pred_labels1==Y_test[:, 1]]
    model2True = pred_labels2[pred_labels2==Y_test[:, 1]]
    print("model1 correct=%d"%(model1True.shape[0]))
    print("model2 correct=%d"%(model2True.shape[0]))
    
    model1True = pred_labels1[pred_labels1==1]
    model2True = pred_labels2[pred_labels2==1]
    print("model1 True=%d"%(model1True.shape[0]))
    print("model2 True=%d"%(model2True.shape[0]))
    
    allt = (pred_labels1==1) & (pred_labels2==1)
    allf = (pred_labels1==0) & (pred_labels2==0)
    m2t = (pred_labels1==0) & (pred_labels2==1)
    m1t = (pred_labels1==1) & (pred_labels2==0)
         
    alltImg = X_test[allt]
    allfImg = X_test[allf]
    m1tImg = X_test[m1t]
    m2tImg = X_test[m2t]
    
    print("allt=%d"%(alltImg.shape[0]))
    print("allf=%d"%(allfImg.shape[0]))
    print("m1t=%d"%(m1tImg.shape[0]))
    print("m2t=%d"%(m2tImg.shape[0]))
    
    print("\n\n***********************")
    print("alltImg: %d"%(alltImg.shape[0]))
    saveImgs(alltImg, "rstImgs/alltImg", zoomScale=4)
    
    print("\n\n***********************")
    print("allfImg: %d"%(allfImg.shape[0]))
    saveImgs(allfImg, "rstImgs/allfImg", zoomScale=4)
    
    print("\n\n***********************")
    print("m1tImg: %d"%(m1tImg.shape[0]))
    saveImgs(m1tImg, "rstImgs/m1tImg", zoomScale=4)
    
    print("\n\n***********************")
    print("m2tImg: %d"%(m2tImg.shape[0]))
    saveImgs(m2tImg, "rstImgs/m2tImg", zoomScale=4)
    

def realDataTest(realOtPath, workPath, tSampleNamePart, tModelNamePart1, tModelNamePart2):
    
    X,Y,s2n = getRealData(realOtPath, workPath, tSampleNamePart)
    
    subNum = 1000
    X = X[:subNum]
    Y = Y[:subNum]
    s2n = s2n[:subNum]
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    
    X_test, Y_test, s2n_test = X, Y, s2n
    y = np.zeros(X_test.shape[0])
    Y_test = np.array([np.logical_not(y), y]).transpose()
    
    from keras.models import load_model
    
    modelName1 = "model_RealFOT_%s.h5"%(tModelNamePart1)
    model = load_model("%s/%s"%(workPath, modelName1))
    Y_pred1 = model.predict(X_test)
    
    modelName2 = "model_RealFOT_%s.h5"%(tModelNamePart2)
    model = load_model("%s/%s"%(workPath, modelName2))
    Y_pred2 = model.predict(X_test)
    
    
    pbb_threshold = 0.5
    pred_labels1 = np.array((Y_pred1[:, 1] > pbb_threshold), dtype = "int")
    pred_labels2 = np.array((Y_pred2[:, 1] > pbb_threshold), dtype = "int")
    
    model1True = pred_labels1[pred_labels1==Y_test[:, 1]]
    model2True = pred_labels2[pred_labels2==Y_test[:, 1]]
    print("model1 correct=%d"%(model1True.shape[0]))
    print("model2 correct=%d"%(model2True.shape[0]))
    
    model1True = pred_labels1[pred_labels1==1]
    model2True = pred_labels2[pred_labels2==1]
    print("model1 True=%d"%(model1True.shape[0]))
    print("model2 True=%d"%(model2True.shape[0]))
    
    diffIdx = pred_labels1!=pred_labels2
    m1t = (pred_labels1==1) & diffIdx
    m1f = (pred_labels1==0) & diffIdx
    m2t = (pred_labels2==1) & diffIdx
    m2f = (pred_labels2==0) & diffIdx
         
    m1tImg = X_test[m1t]
    m1fImg = X_test[m1f]
    m2tImg = X_test[m2t]
    m2fImg = X_test[m2f]
    
    m1tS2n = s2n_test[m1t]
    m1fS2n = s2n_test[m1f]
    m2tS2n = s2n_test[m2t]
    m2fS2n = s2n_test[m2f]
    
    m1tPred = Y_pred1[m1t]
    m1fPred = Y_pred1[m1f]
    m2tPred = Y_pred2[m2t]
    m2fPred = Y_pred2[m2f]
    
    print("m1t=%d"%(m1tImg.shape[0]))
    print("m1f=%d"%(m1fImg.shape[0]))
    print("m2t=%d"%(m2tImg.shape[0]))
    print("m2f=%d"%(m2fImg.shape[0]))
    
    #totImgPath = 'totimg'
    #for i, timg in enumerate(m1tImg):
    #    savePath = "%s/%05d.png"%(totImgPath, i)

    showNum = 100
    falseImg = m1tImg[:showNum]
    falseS2n = m1tS2n[:showNum]
    falsePred = m1tPred[:showNum]
    print("\n\n***********************")
    print("model1 True, model2 False: %d"%(falseImg.shape[0]))
    for i in range(falseImg.shape[0]):
        objWidz = zscale_image(falseImg[i][0])
        tmpWidz = zscale_image(falseImg[i][1])
        resiWidz = zscale_image(falseImg[i][2])
        if objWidz.shape[0] == 0:
            objWidz = falseImg[i][0]
        if tmpWidz.shape[0] == 0:
            tmpWidz = falseImg[i][1]
        if resiWidz.shape[0] == 0:
            resiWidz = falseImg[i][2]
        plt.clf()
        fig, axes = plt.subplots(1, 3, figsize=(6, 2))
        axes.flat[0].imshow(objWidz, interpolation = "nearest", cmap='gray')
        axes.flat[1].imshow(tmpWidz, interpolation = "nearest", cmap='gray')
        axes.flat[2].imshow(resiWidz, interpolation = "nearest", cmap='gray')
        axes.flat[1].set_title("pbb=%.2f,s2n=%.2f"%(falsePred[i][1], falseS2n[i]))
        plt.show()
    
    falseImg = m1fImg[:showNum]
    falseS2n = m1fS2n[:showNum]
    falsePred = m1fPred[:showNum]
    print("\n\n***********************")
    print("model1 True, model2 False: %d"%(falseImg.shape[0]))
    for i in range(falseImg.shape[0]):
        objWidz = zscale_image(falseImg[i][0])
        tmpWidz = zscale_image(falseImg[i][1])
        resiWidz = zscale_image(falseImg[i][2])
        if objWidz.shape[0] == 0:
            objWidz = falseImg[i][0]
        if tmpWidz.shape[0] == 0:
            tmpWidz = falseImg[i][1]
        if resiWidz.shape[0] == 0:
            resiWidz = falseImg[i][2]
        plt.clf()
        fig, axes = plt.subplots(1, 3, figsize=(6, 2))
        axes.flat[0].imshow(objWidz, interpolation = "nearest", cmap='gray')
        axes.flat[1].imshow(tmpWidz, interpolation = "nearest", cmap='gray')
        axes.flat[2].imshow(resiWidz, interpolation = "nearest", cmap='gray')
        axes.flat[1].set_title("pbb=%.2f,s2n=%.2f"%(falsePred[i][1], falseS2n[i]))
        plt.show()
        
def test(totpath, fotpath, workPath, tSampleNamePart, tModelNamePart):
    
    X,Y,s2n = getData2(totpath, fotpath, workPath, tSampleNamePart)
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    
    N_data = X.shape[0]
    N_train = int(N_data * 0.9)
    print("train: %d, test: %d"%(N_train, N_data-N_train))
    X_train, Y_train, s2n_train = X[:N_train], Y[:N_train], s2n[:N_train]
    X_test, Y_test, s2n_test = X[N_train:], Y[N_train:], s2n[N_train:]
    
    from keras.models import load_model
    modelName = "model_RealFOT_%s.h5"%(tModelNamePart)
    model = load_model("%s/%s"%(workPath, modelName))
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
            objWidz = zscale_image(falseImg[i][0])
            tmpWidz = zscale_image(falseImg[i][1])
            resiWidz = zscale_image(falseImg[i][2])
            if objWidz.shape[0] == 0:
                objWidz = falseImg[i][0]
            if tmpWidz.shape[0] == 0:
                tmpWidz = falseImg[i][1]
            if resiWidz.shape[0] == 0:
                resiWidz = falseImg[i][2]
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(6, 2))
            axes.flat[0].imshow(objWidz, interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(tmpWidz, interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(resiWidz, interpolation = "nearest", cmap='gray')
            axes.flat[2].set_title("predicted pbb = " + str(np.round(falsePred[i][1], 2)) + 
                                          ", label = " + str(falseLabel[i, 1]) + 
                                          ", s2n = " + str(falseS2n[i]))
            plt.show()
    
    print("\n\n***********************")
    print("image of False classified as True")
    for i in range(falseImg.shape[0]):
        if falseLabel[i, 1]==0:
            objWidz = zscale_image(falseImg[i][0])
            tmpWidz = zscale_image(falseImg[i][1])
            resiWidz = zscale_image(falseImg[i][2])
            if objWidz.shape[0] == 0:
                objWidz = falseImg[i][0]
            if tmpWidz.shape[0] == 0:
                tmpWidz = falseImg[i][1]
            if resiWidz.shape[0] == 0:
                resiWidz = falseImg[i][2]
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(6, 2))
            axes.flat[0].imshow(objWidz, interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(tmpWidz, interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(resiWidz, interpolation = "nearest", cmap='gray')
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
            objWidz = zscale_image(trueImg[i][0])
            tmpWidz = zscale_image(trueImg[i][1])
            resiWidz = zscale_image(trueImg[i][2])
            if objWidz.shape[0] == 0:
                objWidz = falseImg[i][0]
            if tmpWidz.shape[0] == 0:
                tmpWidz = falseImg[i][1]
            if resiWidz.shape[0] == 0:
                resiWidz = falseImg[i][2]
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(6, 2))
            axes.flat[0].imshow(objWidz, interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(tmpWidz, interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(resiWidz, interpolation = "nearest", cmap='gray')
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
            objWidz = zscale_image(trueImg[i][0])
            tmpWidz = zscale_image(trueImg[i][1])
            resiWidz = zscale_image(trueImg[i][2])
            if objWidz.shape[0] == 0:
                objWidz = falseImg[i][0]
            if tmpWidz.shape[0] == 0:
                tmpWidz = falseImg[i][1]
            if resiWidz.shape[0] == 0:
                resiWidz = falseImg[i][2]
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(6, 2))
            axes.flat[0].imshow(objWidz, interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(tmpWidz, interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(resiWidz, interpolation = "nearest", cmap='gray')
            axes.flat[2].set_title("predicted pbb = " + str(np.round(truePred[i][1], 2)) + 
                                          ", label = " + str(trueLabel[i, 1]) + 
                                          ", s2n = " + str(trueS2n[i]))
            plt.show()
            tnum = tnum + 1
            if tnum>showNum:
                break

    
if __name__ == "__main__":
    
    train()



