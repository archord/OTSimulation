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

def getData(tpath):
    #tpath1 = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data/CombZ_0_otimg.npz"
    tdata1 = np.load(tpath)
    totImg = tdata1['tot']
    fotImg = tdata1['fot']
    totSize = totImg.shape[0]
    fotSize = fotImg.shape[0]
    totLabel = np.ones(totSize)
    fotLabel = np.zeros(fotSize)
    X = np.concatenate((totImg, fotImg), axis=0)
    y = np.concatenate((totLabel, fotLabel), axis=0)
    Y = np.array([np.logical_not(y), y]).transpose()

    XY = []
    for i in range(Y.shape[0]):
        XY.append((X[i],Y[i]))
    XY = np.array(XY)
    np.random.shuffle(XY)
    
    X = []
    Y = []
    for i in range(XY.shape[0]):
        X.append(XY[i][0])
        Y.append(XY[i][1])
    X = np.array(X)
    Y = np.array(Y)
    print(X.shape)
    print(Y.shape)
    return X, Y
    
def getData2(tpath):
    
    timgbinPath = '/home/xy/Downloads/myresource/deep_data2/simot/SIM_IMG_ALL_bin.npz'
    if os.path.exists(timgbinPath):
        print("bin file exist, read from %s"%(timgbinPath))
        timgbin = np.load(timgbinPath)
        Xs = timgbin['Xs']
        Ys = timgbin['Ys']
    else:
        #tpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data"
        tdirs = os.listdir(tpath)
        tdirs.sort()
        tdirNum =0
        Xs = np.array([])
        Ys = np.array([])
        for fname in tdirs:
            tpath2 = "%s/%s"%(tpath, fname)
            #print(tpath2)
            tdata1 = np.load(tpath2)
            totImg = tdata1['tot']
            fotImg = tdata1['fot']
            totSize = totImg.shape[0]
            fotSize = fotImg.shape[0]
            totLabel = np.ones(totSize)
            fotLabel = np.zeros(fotSize)
            X = np.concatenate((totImg, fotImg), axis=0)
            y = np.concatenate((totLabel, fotLabel), axis=0)
            Y = np.array([np.logical_not(y), y]).transpose()

            XY = []
            for i in range(Y.shape[0]):
                XY.append((X[i],Y[i]))
            XY = np.array(XY)
            np.random.shuffle(XY)
            X = []
            Y = []

            for i in range(XY.shape[0]):
                X.append(XY[i][0])
                Y.append(XY[i][1])
            X = np.array(X)
            Y = np.array(Y)
            if Xs.shape[0]==0:
                Xs = X
            else:
                Xs = np.concatenate((Xs, X))

            if Ys.shape[0]==0:
                Ys = Y
            else:
                Ys = np.concatenate((Ys, Y))

            tdirNum = tdirNum+1
        
        np.savez_compressed(timgbinPath, Xs=Xs, Ys=Ys)
        print("save bin fiel to %s"%(timgbinPath))
    print("total read image file %d"%(tdirNum))
        
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
    
    tpath = "/home/xy/Downloads/myresource/deep_data2/simot/rest_data"
    X,Y = getData2(tpath)
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
    model.save("/home/xy/Downloads/myresource/deep_data2/simot/train_model/m0907-gpu-all-128.h5")
    
    Y_pred = model.predict(X_test)
    
    pbb_threshold = 0.5
    pred_labels = np.array((Y_pred[:, 1] > pbb_threshold), dtype = "int")
    print("Correctly classified %d out of %d"%((pred_labels == Y_test[:, 1].astype(int)).sum(), Y_test.shape[0]))
    print("accuracy = %f"%(1.*(pred_labels == Y_test[:, 1].astype(int)).sum() / Y_test.shape[0]))
    
