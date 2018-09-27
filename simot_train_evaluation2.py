# -*- coding: utf-8 -*-
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

#%matplotlib inline

def getImgStamp(imgArray, size=12):
    
    rst = np.array([])
    if len(imgArray.shape)==4 and imgArray.shape[0]>0:
        padding = 1
        imgSize = imgArray[0][0][0].shape[0]
        ctrIdx = math.ceil(imgSize/2.0) - 1
        halfWid = math.floor(size/2.0)
        minIdx = ctrIdx - halfWid - padding
        maxIdx = ctrIdx + halfWid - padding
        
        rstImgs = []
        for timgs in imgArray:
            img1 = timgs[0][minIdx:maxIdx,minIdx:maxIdx]
            img2 = timgs[1][minIdx:maxIdx,minIdx:maxIdx]
            img3 = timgs[2][minIdx:maxIdx,minIdx:maxIdx]
            rstImgs.append([img1,img2,img3])
        rst = np.array(rstImgs)
    return rst
    
def getData(tpath, destPath):
    
    timgbinPath = '%s/SIM_IMG_ALL_bin12.npz'%(destPath)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['X']
        Y = timgbin['Y']
        s2n = timgbin['s2n']
    else:
        #tpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0924"
        tdirs = os.listdir(tpath)
        tdirs.sort()
        
        totImgs = np.array([])
        fotImgs = np.array([])
        ts2ns = np.array([])
        fs2ns = np.array([])
        for fname in tdirs:
            if fname[-7:]=='fot.npz':
                continue
            tfhead = fname[:-7]
            totPath = "%s/%stot.npz"%(tpath, tfhead)
            fotPath = "%s/%sfot.npz"%(tpath, tfhead)
            print(totPath)
            tdata1 = np.load(totPath)
            fdata1 = np.load(fotPath)
            
            totImg = tdata1['tot']
            ts2n = tdata1['ts2n']
            fotImg = fdata1['fot']
            fs2n = fdata1['fs2n']
            
            totImg = getImgStamp(totImg)
            fotImg = getImgStamp(fotImg)
            
            if totImgs.shape[0]==0:
                totImgs = totImg
                fotImgs = fotImg
                ts2ns = ts2n
                fs2ns = fs2n
            else:
                totImgs = np.concatenate((totImgs, totImg), axis=0)
                fotImgs = np.concatenate((fotImgs, fotImg), axis=0)
                ts2ns = np.concatenate((ts2ns, ts2n), axis=0)
                fs2ns = np.concatenate((fs2ns, fs2n), axis=0)
            #break
        
        totNum = totImgs.shape[0]
        fotNum = fotImgs.shape[0]
        if totNum>fotNum:
            totImgs = totImgs[0:fotNum]
            ts2ns = ts2ns[0:fotNum]
        elif totNum<fotNum:
            fotImgs = fotImgs[0:totNum]
            fs2ns = fs2ns[0:totNum]
        
        totSize = totImgs.shape[0]
        fotSize = fotImgs.shape[0]
        totLabel = np.ones(totSize)
        fotLabel = np.zeros(fotSize)
        X = np.concatenate((totImgs, fotImgs), axis=0)
        s2n = np.concatenate((ts2ns, fs2ns), axis=0)
        y = np.concatenate((totLabel, fotLabel), axis=0)
        Y = np.array([np.logical_not(y), y]).transpose()
            
        XY = []
        for i in range(Y.shape[0]):
            XY.append((X[i],Y[i],s2n[i]))
        XY = np.array(XY)
        np.random.shuffle(XY)
        
        X = []
        Y = []
        s2n = []
        for i in range(XY.shape[0]):
            X.append(XY[i][0])
            Y.append(XY[i][1])
            s2n.append(XY[i][2])
        X = np.array(X)
        Y = np.array(Y)
        s2n = np.array(s2n)
        
        np.savez_compressed(timgbinPath, X=X, Y=Y, s2n=s2n)
        print("save bin fiel to %s"%(timgbinPath))
    return X, Y, s2n

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
    
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    X,Y,s2n = getData(tpath1, workPath)
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
    
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    X,Y,s2n = getData(tpath1, workPath)
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

def viewData():
    
    tpath1 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data_0924"
    tpath2 = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2"
    
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    X,Y,s2n = getData(tpath1, workPath)
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    
    showNum=50
    tnum = 0
    print("\n\n***********************")
    print("True image")
    for i in range(X.shape[0]):
        if Y[i, 1]==1:
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(3, 3))
            axes.flat[0].imshow(X[i][0], interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(X[i][1], interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(X[i][2], interpolation = "nearest", cmap='gray')
            axes.flat[2].set_title("predicted label = " + str(Y[i, 1]) + 
                                          ", s2n = " + str(s2n[i]))
            plt.show()
            tnum = tnum + 1
            if tnum>showNum:
                break
    
    tnum = 0
    print("\n\n***********************")
    print("False image")
    for i in range(X.shape[0]):
        if Y[i, 1]==0:
            plt.clf()
            fig, axes = plt.subplots(1, 3, figsize=(3, 3))
            axes.flat[0].imshow(X[i][0], interpolation = "nearest", cmap='gray')
            axes.flat[1].imshow(X[i][1], interpolation = "nearest", cmap='gray')
            axes.flat[2].imshow(X[i][2], interpolation = "nearest", cmap='gray')
            axes.flat[2].set_title("predicted label = " + str(Y[i, 1]) + 
                                          ", s2n = " + str(s2n[i]))
            plt.show()
            tnum = tnum + 1
            if tnum>showNum:
                break


def readStampFromFits(filename, size=12):
    
    rst = np.array([])
    with fits.open(filename,memmap=False) as ft:
        
        data = ft[0].data
        padding = -1
        imgSize = data.shape[0]
        ctrIdx = math.ceil(imgSize/2.0) - 1
        halfWid = math.floor(size/2.0)
        minIdx = ctrIdx - halfWid - padding
        maxIdx = ctrIdx + halfWid - padding
        rst = data[minIdx:maxIdx,minIdx:maxIdx]
        
    return rst
    
def getRealData(destPath):
    
    from gwac_util import zscale_image
    ot2path = '/home/xy/Downloads/myresource/deep_data2/simot/ot2_img_collection_180906_20180907'
    ot2listFile = '%s/list.txt'%(ot2path)
    ot2list = np.genfromtxt(ot2listFile,dtype='str')
    print(ot2list.shape)
    print(ot2list[:3])
    
    X = []
    badImgNum = 0
    badIdx = []
    
    #timgbinPath = '%s/gwac_otimg_nozscale.npz'%(destPath)
    timgbinPath = '%s/gwac_otimg.npz'%(destPath)
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        X = timgbin['ot']
        ot2prop = timgbin['ot2prop']
    else:
        for i in range(ot2list.shape[0]):
            tot2 = ot2list[i]
            objPath = "%s/%s"%(ot2path, tot2[1])
            refPath = "%s/%s"%(ot2path, tot2[2])
            diffPath = "%s/%s"%(ot2path, tot2[3])
    
            objImg = readStampFromFits(objPath)
            refImg = readStampFromFits(refPath)
            diffImg = readStampFromFits(diffPath)
            
            if objImg.shape[0]==0 or refImg.shape[0]==0 or diffImg.shape[0]==0:
                continue
            
            objImgz = zscale_image(objImg)
            refImgz = zscale_image(refImg)
            diffImgz = zscale_image(diffImg)
            '''
            objImgz = objImg
            refImgz = refImg
            diffImgz = diffImg
            '''
            #异常残差图像处理，如果scale失败：1）等于原diffImg；2）直接量化到255
            if diffImgz.shape[0]!=12 or diffImgz.shape[1]!=12:
                print("%d, %s"%(i, tot2[1]))
                badIdx.append(i)
                tmin = np.min(diffImg)
                tmax = np.max(diffImg)
                diffImgz=(((diffImg-tmin)/(tmax-tmin))*255).astype(np.uint8)
                #diffImgz = diffImg
                badImgNum = badImgNum + 1
    
            X.append([objImgz, refImgz, diffImgz])
        
        X = np.array(X)
        '''
        for i in range(X.shape[0]):
            tot2 = ot2list[i]
            tlabel = tot2[4]
            ttype = tot2[5]
            if ttype=='2':
                fig, axes = plt.subplots(1, 3, figsize=(3, 1))
                axes.flat[0].imshow(X[i][0], cmap='gray')
                axes.flat[1].imshow(X[i][1], cmap='gray')
                axes.flat[2].imshow(X[i][2], cmap='gray')
                axes.flat[1].set_title("%d, %s, look=%s, type=%s"%(i, tot2[1][:14], tlabel, ttype))
                plt.show()
        '''
        ot2prop = ot2list
        print("save bin fiel to %s"%(timgbinPath))
        np.savez_compressed(timgbinPath, ot=X, ot2prop = ot2prop)
        print("bad image %d"%(badImgNum))
    return X, ot2prop
    
def realDataTest():
        
    dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    X, ot2prop = getRealData(workPath)
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

if __name__ == "__main__":
    
    train()



