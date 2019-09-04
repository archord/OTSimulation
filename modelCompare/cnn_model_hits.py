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

#eval, transpose, cast_to_floatx, variable
def rotate90(x, num=1):
    
    tf_session = K.get_session()
    print(K.shape(x).eval())
    
    obj = x[:,0]
    ref = x[:,1]
    resi = x[:,2]
    print(K.shape(obj).eval())
    
    obj1 = K.eval(obj)
    ref1 = K.eval(ref)
    resi1 = K.eval(resi)
    
    obj1 = np.rot90(obj1, num)
    ref1 = np.rot90(ref1, num)
    resi1 = np.rot90(resi1, num)
    
    obj = K.variable(obj1)
    ref = K.variable(ref1)
    resi = K.variable(resi1)
    
    con = concatenate([obj, ref, resi], axis=1)

    return con
    
def createModel0():
    
    K.set_image_data_format('channels_first')
    #K.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model3 = Cropping2D(cropping=28,data_format='channels_first')(input0) #8*8
    model3 = Lambda(rotate90)(model3)
    model3 = Conv2D(18, (3, 3), padding='same', activation='relu')(model3)
    model3 = Conv2D(18, (3, 3), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(24, (2, 2), padding='same', activation='relu')(model3)
    model3 = Conv2D(24, (2, 2), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Flatten()(model3)
    out = Dense(64, activation='relu')(model3)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0

def createModel():
    
    K.set_image_data_format('channels_first')
    #K.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=26,data_format='channels_first')(input0) #12*12
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    
    model2 = Cropping2D(cropping=16,data_format='channels_first')(input0) #32*32
    model2 = Conv2D(8, (4, 4), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(20, (3, 3), padding='same', activation='relu')(model2)
    model2 = Conv2D(20, (3, 3), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(40, (2, 2), padding='same', activation='relu')(model2)
    model2 = Conv2D(40, (2, 2), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Flatten()(model2)

    model3 = Cropping2D(cropping=28,data_format='channels_first')(input0) #8*8
    model3 = Lambda(grayInverse)(model3)
    model3 = Conv2D(18, (3, 3), padding='same', activation='relu')(model3)
    model3 = Conv2D(18, (3, 3), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(24, (2, 2), padding='same', activation='relu')(model3)
    model3 = Conv2D(24, (2, 2), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Flatten()(model3)
    
    conc = Concatenate()([model1, model2, model3])
    out = Dense(100, activation='relu')(conc)
    out = Dense(100, activation='relu')(out)
    '''
    conc = Concatenate()([model1, model2])
    out = Dense(64, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
        '''
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0
    
