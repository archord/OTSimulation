# -*- coding: utf-8 -*-

import numpy as np
import os
import matplotlib.pyplot as plt
from IPython.display import SVG
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.utils.vis_utils import plot_model
from keras.utils.vis_utils import model_to_dot
import keras

    
def getData(tpath1, tpath2):
    
    timgbinPath = '/home/xy/Downloads/myresource/deep_data2/simot/SIM_IMG_ALL_with_OT2F_bin2.npz'
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        Xs = timgbin['Xs']
        Ys = timgbin['Ys']
    else:
        #tpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data"
        tdirs = os.listdir(tpath1)
        tdirs.sort()
        tdirNum =0
        
        totImgs = np.array([])
        fotImgs = np.array([])
        totLabels = np.array([])
        fotLabels = np.array([])
        for fname in tdirs:
            tpath11 = "%s/%s"%(tpath1, fname)
            print(tpath11)
            tdata1 = np.load(tpath11)
            totImg = tdata1['tot']
            fotImg = tdata1['fot']
            totSize = totImg.shape[0]
            fotSize = fotImg.shape[0]
            totLabel = np.ones(totSize)
            fotLabel = np.zeros(fotSize)
            
            if totImgs.shape[0]==0:
                totImgs = totImg
            else:
                totImgs = np.concatenate((totImgs, totImg), axis=0)
            if fotImgs.shape[0]==0:
                fotImgs = fotImg
            else:
                fotImgs = np.concatenate((fotImgs, fotImg), axis=0)
            if totLabels.shape[0]==0:
                totLabels = totLabel
            else:
                totLabels = np.concatenate((totLabels, totLabel), axis=0)
            if fotLabels.shape[0]==0:
                fotLabels = fotLabel
            else:
                fotLabels = np.concatenate((fotLabels, fotLabel), axis=0)
            
            tdirNum = tdirNum+1
        print("total read image file %d"%(tdirNum))
        print(totImgs.shape)
        print(totLabels.shape)
        print(fotImgs.shape)
        print(fotLabels.shape)
        
        totNum = totImgs.shape[0]
        tdirs = os.listdir(tpath2)
        tdirs.sort()
        tdirNum =0
        
        timgs = np.array([])
        tprops = np.array([])
        tnum = 0
        for fname in tdirs:
            tpath21 = "%s/%s"%(tpath2, fname)
            print(tpath21)
            tdata1 = np.load(tpath21)
            imgs = tdata1['imgs']
            props = tdata1['props']
            
            if timgs.shape[0]==0:
                timgs = imgs
            else:
                timgs = np.concatenate((timgs, imgs), axis=0)
            if tprops.shape[0]==0:
                tprops = props
            else:
                tprops = np.concatenate((tprops, props), axis=0)
                
            tnum = tnum + imgs.shape[0]
            if tnum>totNum/4:
                break
        
        print(timgs.shape)
        print(tprops.shape)
        tlabel = tprops[:,4].astype(np.int)
        fot2Idx = tlabel>1
        fotImg2 = timgs[fot2Idx]
        fotLabel2 = tlabel[fot2Idx]
        print(fotImg2.shape)
        print(fotLabel2.shape)
        
        selFOTNum = totNum - fotLabel2.shape[0]
        fotImg3 = fotImgs[:selFOTNum]
        fotLabel3 = fotLabels[:selFOTNum]
        
        fotImgs = np.concatenate((fotImg2, fotImg3), axis=0)
        fotLabels = np.concatenate((fotLabel2, fotLabel3), axis=0)
        print(totImgs.shape)
        print(totLabels.shape)
        print(fotImgs.shape)
        print(fotLabels.shape)
            
        Xs = np.concatenate((totImgs, fotImgs), axis=0)
        Ys = np.concatenate((totLabels, fotLabels), axis=0)
        Ys = np.array([np.logical_not(Ys), Ys]).transpose()
        
        XY = []
        for i in range(Ys.shape[0]):
            XY.append((Xs[i],Ys[i]))
        XY = np.array(XY)
        np.random.shuffle(XY)
        Xs = []
        Ys = []

        for i in range(XY.shape[0]):
            Xs.append(XY[i][0])
            Ys.append(XY[i][1])
        Xs = np.array(Xs)
        Ys = np.array(Ys)
            
        np.savez_compressed(timgbinPath, Xs=Xs, Ys=Ys)
        print("save bin fiel to %s"%(timgbinPath))
        
    return Xs, Ys

def createModel():
    
    model = Sequential ()
    model.add(ZeroPadding2D((3, 3), input_shape = (3, 21, 21)))
    model.add(Convolution2D(32, 4, 4))
    model.add(Activation('relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(32, 3, 3))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size =(2, 2)))
    
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(64, 3, 3))
    model.add(Activation('relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(64, 3, 3))
    model.add(Activation('relu'))
    model.add(ZeroPadding2D((1, 1)))
    model.add(Convolution2D(64, 3, 3))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size =(2, 2)))
    
    model.add(Flatten())
    model.add(Dense(64))
    model.add(Activation('relu'))
    model.add(Dense(64))
    model.add(Activation('relu'))
    model.add(Dense(2))
    model.add(Activation('softmax'))
    
    return model

if __name__ == "__main__":
    
    tpath1 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data"
    tpath2 = "/home/xy/Downloads/myresource/deep_data2/gwac_ot2"
    X,Y = getData(tpath1, tpath2)
    print(X.shape)
    print(Y.shape)

    
    keras.backend.set_image_dim_ordering('th')
    model = createModel()    
    #optimizer = keras.optimizers.SGD(lr=0.0001, decay=1e-6, momentum=0.9, nesterov=True)
    optimizer = keras.optimizers.Adam(lr=0.0001, beta_1=0.9, beta_2=0.999,decay=0.0)
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    
    N_data = X.shape[0]
    N_train = int(N_data * 0.9)
    
    X_train, Y_train = X[:N_train], Y[:N_train]
    X_test, Y_test = X[N_train:], Y[N_train:]
    print("train: %d, test: %d"%(N_train, N_data-N_train))
    
    model.fit(X_train, Y_train, batch_size=128, nb_epoch=5, validation_split=0.2)
    #model.save_weights("/home/xy/Downloads/myresource/deep_data2/simot/train_model/m0907.h5")
    model.save("/home/xy/Downloads/myresource/deep_data2/simot/train_model/m180912-gpu-all-128.h5")
    
    Y_pred = model.predict(X_test)
    
    pbb_threshold = 0.5
    pred_labels = np.array((Y_pred[:, 1] > pbb_threshold), dtype = "int")
    print("Correctly classified %d out of %d"%((pred_labels == Y_test[:, 1].astype(int)).sum(), Y_test.shape[0]))
    print("accuracy = %f"%(1.*(pred_labels == Y_test[:, 1].astype(int)).sum() / Y_test.shape[0]))
