# -*- coding: utf-8 -*-
from astropy.io import fits
import numpy as np
import math
import os
import shutil
from datetime import datetime
import matplotlib.pyplot as plt
import keras
from DataPreprocess import getData2, getRealData, saveImgs, getElongData
from gwac_util import zscale_image
import traceback
import cnn_model
    

#train with real Sample of False miss classify as True
def train(totpath, fotpath, workPath, tSampleNamePart):
    
    X,Y,s2n = getData2(totpath, fotpath, workPath, tSampleNamePart)
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    
    N_data = X.shape[0]
    N_train = int(N_data * 0.9)
    print("train: %d, test: %d"%(N_train, N_data-N_train))
    X_train, Y_train, s2n_train = X[:N_train], Y[:N_train], s2n[:N_train]
    X_test, Y_test, s2n_test = X[N_train:], Y[N_train:], s2n[N_train:]
    
    #model = createModel()    
    #optimizer = keras.optimizers.SGD(lr=0.0001, decay=1e-6, momentum=0.9, nesterov=True)
    optimizer = keras.optimizers.Adam(lr=0.00001, beta_1=0.9, beta_2=0.999,decay=0.0)
    
    model = cnn_model.createModel_64_1()
    tModelNamePart = "createModel_64_1"
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    
    model.fit(X_train, Y_train, batch_size=128, epochs=100, validation_split=0.2)
    modelName = "model_RealFOT_%s.h5"%(tModelNamePart)
    model.save("%s/%s"%(workPath, modelName))
    
    model = cnn_model.createModel_64_2()
    tModelNamePart = "createModel_64_2"
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    
    model.fit(X_train, Y_train, batch_size=128, epochs=100, validation_split=0.2)
    modelName = "model_RealFOT_%s.h5"%(tModelNamePart)
    model.save("%s/%s"%(workPath, modelName))
    
    model = cnn_model.createModel_12_36()
    tModelNamePart = "createModel_12_36"
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
    #dateStr = '20190811'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    tSampleNamePart = "64_fot10w_%s"%(dateStr)
    #tModelNamePart = "64_100_fot10w_%s_dropout"%(dateStr)
    #tModelNamePart = "8_100_fot10w_%s_dropout"%(dateStr)
    
    train(totpath, fotpath, workPath, tSampleNamePart)
    

    
if __name__ == "__main__":
    
    train()



