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
#https://keras.io/backend/#reverse
def rotate1(x):
    y = K.reverse(x, 2)
    return y
def rotate2(x):
    y = K.reverse(x, 3)
    return y
def rotate3(x):
    y = K.reverse(x, 2)
    y = K.reverse(y, 3)
    return y

def createModelHits():
    
    K.set_image_data_format('channels_first')
    #K.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model0 = Cropping2D(cropping=20,data_format='channels_first')(input0) #24*24
    
    model1 = Lambda(rotate1)(model0)
    model1 = Conv2D(32, (4, 4), padding='same', activation='relu')(model1)
    model1 = Conv2D(32, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    
    model2 = Lambda(rotate2)(model0)
    model2 = Conv2D(32, (4, 4), padding='same', activation='relu')(model2)
    model2 = Conv2D(32, (3, 3), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Flatten()(model2)

    model3 = Lambda(rotate3)(model0)
    model3 = Conv2D(32, (4, 4), padding='same', activation='relu')(model3)
    model3 = Conv2D(32, (3, 3), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(64, (3, 3), padding='same', activation='relu')(model3)
    model3 = Conv2D(64, (3, 3), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Flatten()(model3)
    
    model4 = Conv2D(32, (4, 4), padding='same', activation='relu')(model0)
    model4 = Conv2D(32, (3, 3), padding='same', activation='relu')(model4)
    model4 = MaxPooling2D(pool_size =(2, 2))(model4)
    model4 = Conv2D(64, (3, 3), padding='same', activation='relu')(model4)
    model4 = Conv2D(64, (3, 3), padding='same', activation='relu')(model4)
    model4 = MaxPooling2D(pool_size =(2, 2))(model4)
    model4 = Flatten()(model4)
    
    conc = Concatenate()([model1, model2, model3, model4])
    out = Dense(64, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0
    

def createModelHits2():
    
    K.set_image_data_format('channels_first')
    #K.set_image_dim_ordering('th')
    
    input1 = Input(shape=(3, 32, 32))
    input2 = Input(shape=(3, 32, 32))
    input3 = Input(shape=(3, 32, 32))
    input4 = Input(shape=(3, 32, 32))
    '''
    model1 = Cropping2D(cropping=20,data_format='channels_first')(input1) #24*24
    model2 = Cropping2D(cropping=20,data_format='channels_first')(input2) #24*24
    model3 = Cropping2D(cropping=20,data_format='channels_first')(input3) #24*24
    model4 = Cropping2D(cropping=20,data_format='channels_first')(input4) #24*24
    '''
    model1 = Conv2D(32, (4, 4), padding='same', activation='relu')(input1)
    model1 = Conv2D(32, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    
    model2 = Conv2D(32, (4, 4), padding='same', activation='relu')(input2)
    model2 = Conv2D(32, (3, 3), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Flatten()(model2)

    model3 = Conv2D(32, (4, 4), padding='same', activation='relu')(input3)
    model3 = Conv2D(32, (3, 3), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(64, (3, 3), padding='same', activation='relu')(model3)
    model3 = Conv2D(64, (3, 3), padding='same', activation='relu')(model3)
    model3 = Conv2D(64, (3, 3), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Flatten()(model3)
    
    model4 = Conv2D(32, (4, 4), padding='same', activation='relu')(input4)
    model4 = Conv2D(32, (3, 3), padding='same', activation='relu')(model4)
    model4 = MaxPooling2D(pool_size =(2, 2))(model4)
    model4 = Conv2D(64, (3, 3), padding='same', activation='relu')(model4)
    model4 = Conv2D(64, (3, 3), padding='same', activation='relu')(model4)
    model4 = Conv2D(64, (3, 3), padding='same', activation='relu')(model4)
    model4 = MaxPooling2D(pool_size =(2, 2))(model4)
    model4 = Flatten()(model4)
    
    conc = Concatenate()([model1, model2, model3, model4])
    out = Dense(64, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=[input1,input2,input3,input4], outputs=out)
        
    return model0
