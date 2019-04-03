# -*- coding: utf-8 -*-
import numpy as np
import math
import os
import shutil
from datetime import datetime
import keras
from keras.models import Sequential, Model
from keras.layers import Dense, Dropout, Activation, Flatten, Input
from keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D, Concatenate, Cropping2D, Lambda
from keras import backend as K
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

def ot_generator(dataPath):
    batch_size = 10000
    index = 0
    curDataBlock = np.array([])
    while True:
        startIdx = index*batch_size
        endIdx = (index+1)*batch_size
        fileStartIdx = math.floor(startIdx/100000)+1
        fileEndIdx = math.floor(endIdx/100000)+1
                
        tpath = '%s/train%d.npz'%(dataPath, fileEndIdx)
        if index==0:
            curDataBlock = np.load(tpath)
            
        if fileStartIdx==fileEndIdx:
            X = curDataBlock['X'][startIdx:endIdx]
            Y = curDataBlock['Y'][startIdx:endIdx]
        else:
            lastDataBlock = curDataBlock
            curDataBlock = np.load(tpath)
            X1 = lastDataBlock['X'][startIdx:]
            Y1 = lastDataBlock['Y'][startIdx:]
            X2 = curDataBlock['X'][:endIdx]
            Y2 = curDataBlock['Y'][:endIdx]
            
            X = np.concatenate((X1,X2), axis=0)
            Y = np.concatenate((Y1,Y2), axis=0)
        
        index += 1
        if index>=800000/batch_size:
            index = 0
        yield (X, Y)
                
def doAll():
    
    #dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    dateStr = '20190403'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    tModelNamePart = "80w_%s_dropout_train1"%(dateStr) #944376
    train(workPath, tModelNamePart)
   
def train(workPath, tModelNamePart):
    
    dataPath = "%s/data"%(workPath)
    tdata = np.load("%s/valid.npz"%(dataPath))
    validteData = (tdata['X'], tdata['Y'])
    
    model = createModel()    
    #optimizer = keras.optimizers.SGD(lr=0.0001, decay=1e-6, momentum=0.9, nesterov=True)
    optimizer = keras.optimizers.Adam(lr=0.00001, beta_1=0.9, beta_2=0.999,decay=0.0)
    model.compile(loss='mean_squared_error', optimizer=optimizer)
    
    #model.fit(X_train, Y_train, batch_size=128, epochs=100, validation_split=0.2)
    model.fit_generator(ot_generator(dataPath), steps_per_epoch=6250, epochs=1, validation_data=validteData, verbose=1)
    modelName = "model_%s.h5"%(tModelNamePart)
    model.save("%s/%s"%(workPath, modelName))

    
if __name__ == "__main__":
    
    train()



