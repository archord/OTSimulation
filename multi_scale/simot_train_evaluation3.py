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
from keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D, Concatenate, Cropping2D, Lambda
from keras import backend as K
from DataPreprocess import getData2, getRealData, saveImgs, getElongData
from gwac_util import zscale_image
import traceback
    
def createModel():
    
    K.set_image_data_format('channels_first')
    #K.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=28,data_format='channels_first')(input0) #8*8
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(24, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    
    model2 = Conv2D(18, (5, 5), activation='relu')(input0) #64*64
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
    
    for i in range(3):
        model.fit(X_train, Y_train, batch_size=128, epochs=50, validation_split=0.2)
        modelName = "model_RealFOT_%s_1.h5"%(tModelNamePart, (i+1))
        model.save("%s/%s"%(workPath, modelName))
        

def doAll():
    
    fotpath = "/home/xy/Downloads/myresource/deep_data2/simot/multi_scale_20190120"
    totpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_20190120"
    
    #dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    dateStr = '20190402'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    tSampleNamePart = "branch2_100w_%s"%(dateStr)
    tModelNamePart = "branch2_dropout_%s"%(dateStr)
    #tModelNamePart = "8_100_fot10w_%s_dropout"%(dateStr)
    train(totpath, fotpath, workPath, tSampleNamePart, tModelNamePart)
    test(totpath, fotpath, workPath, tSampleNamePart, tModelNamePart)
    
    
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
    K.set_image_data_format('channels_first')
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



