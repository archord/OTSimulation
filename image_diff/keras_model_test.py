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
from DataPreprocess import getData2

#https://stackoverflow.com/questions/43196636/how-to-concatenate-two-layers-in-keras
#https://keras.io/getting-started/functional-api-guide/
def createModel():
    
    keras.backend.set_image_dim_ordering('th')
    model1 = Sequential ()
    model1.add(Conv2D(18, (3, 3), padding='same', activation='relu', input_shape=(3, 8, 8)))
    model1.add(Conv2D(18, (3, 3), padding='same', activation='relu'))
    model1.add(MaxPooling2D(pool_size =(2, 2)))
    model1.add(Conv2D(24, (3, 3), padding='same', activation='relu'))
    model1.add(Conv2D(36, (3, 3), padding='same', activation='relu'))
    model1.add(MaxPooling2D(pool_size =(2, 2)))
    model1.add(Flatten())
    
    model2 = Sequential ()
    model2.add(Conv2D(18, (5, 5), activation='relu', input_shape=(3, 64, 64)))
    model2.add(MaxPooling2D(pool_size =(3, 3)))
    model2.add(Conv2D(36, (4, 4), padding='same', activation='relu'))
    model2.add(Conv2D(36, (4, 4), padding='same', activation='relu'))
    model2.add(MaxPooling2D(pool_size =(2, 2)))
    model2.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
    model2.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
    model2.add(MaxPooling2D(pool_size =(2, 2)))
    model2.add(Flatten())
    
    conc = Concatenate()([model1.output, model2.output])
    out = Dense(64, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    #out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model([model1.input, model2.input], out)
        
    return model0
    
def createModel2():
    
    keras.backend.set_image_dim_ordering('th')
    model1 = Sequential ()
    model1.add(Cropping2D(cropping=28,input_shape=(3, 64, 64),data_format='channels_first'))
    model1.add(Conv2D(18, (3, 3), padding='same', activation='relu'))
    model1.add(Conv2D(18, (3, 3), padding='same', activation='relu'))
    model1.add(MaxPooling2D(pool_size =(2, 2)))
    model1.add(Conv2D(24, (3, 3), padding='same', activation='relu'))
    model1.add(Conv2D(36, (3, 3), padding='same', activation='relu'))
    model1.add(MaxPooling2D(pool_size =(2, 2)))
    model1.add(Flatten())
    
    model2 = Sequential ()
    model2.add(Conv2D(18, (5, 5), activation='relu', input_shape=(3, 64, 64)))
    model2.add(MaxPooling2D(pool_size =(3, 3)))
    model2.add(Conv2D(36, (4, 4), padding='same', activation='relu'))
    model2.add(Conv2D(36, (4, 4), padding='same', activation='relu'))
    model2.add(MaxPooling2D(pool_size =(2, 2)))
    model2.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
    model2.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
    model2.add(MaxPooling2D(pool_size =(2, 2)))
    model2.add(Flatten())
    
    conc = Concatenate()([model1.output, model2.output])
    out = Dense(64, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    #out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model([model1.input, model2.input], out)
        
    return model0
    
def createModel3():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=28,data_format='channels_first')(input0)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(24, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (3, 3), padding='same', activation='relu')(model1)
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
    #out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0

    
if __name__ == "__main__":
    
    from IPython.display import SVG
    from keras.utils.vis_utils import plot_model
    from keras.utils.vis_utils import model_to_dot
    
    model = createModel3() 
    #plot_model(model, show_shapes=True, to_file='model.png')
    plot_model(model, to_file='model.png')
    SVG(model_to_dot(model, show_shapes = True).create(prog='dot', format='svg'))



