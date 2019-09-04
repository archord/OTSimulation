# -*- coding: utf-8 -*-
import keras
from keras.models import Sequential, Model
from keras.layers import Dense, Dropout, Activation, Flatten, Input
from keras.layers import Conv2D, MaxPooling2D, ZeroPadding2D, Concatenate, Cropping2D

def createModel_08():
    
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

def createModel_12():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=26,data_format='channels_first')(input0) #12*12
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

def createModel_16():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=24,data_format='channels_first')(input0) #16*16
    model1 = Conv2D(18, (5, 5), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (5, 5), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(48, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(48, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    out = Dense(64, activation='relu')(model1)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0

def createModel_32():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=24,data_format='channels_first')(input0) #32*32
    model1 = Conv2D(18, (5, 5), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (5, 5), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(48, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(48, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(64, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(64, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    out = Dense(96, activation='relu')(model1)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0

def createModel_64_1():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Conv2D(18, (5, 5), activation='relu')(input0)
    model1 = MaxPooling2D(pool_size =(3, 3))(model1)
    model1 = Conv2D(36, (4, 4), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (4, 4), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    out = Dense(64, activation='relu')(model1)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0

def createModel_64_2():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Conv2D(18, (5, 5), activation='relu')(input0)
    model1 = MaxPooling2D(pool_size =(3, 3))(model1)
    model1 = Conv2D(48, (4, 4), padding='same', activation='relu')(model1)
    model1 = Conv2D(48, (4, 4), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(64, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(96, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(96, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    out = Dense(128, activation='relu')(model1)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0
    
def createModel_08_64():
    
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

def createModel_12_36():
    
    from keras.layers import concatenate
    from keras import backend as K
    K.set_image_data_format('channels_first')
    #K.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=26,data_format='channels_first')(input0) #12*12
    
    model2 = Cropping2D(cropping=14,data_format='channels_first')(input0) #36*36
    #model2 = Conv2D(8, (4, 4), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(3, 3))(model2)
    conc = concatenate([model1, model2], axis=1)
    
    conc = Conv2D(48, (3, 3), padding='same', activation='relu')(conc)
    conc = Conv2D(48, (3, 3), padding='same', activation='relu')(conc)
    conc = MaxPooling2D(pool_size =(2, 2))(conc)
    conc = Conv2D(64, (2, 2), padding='same', activation='relu')(conc)
    conc = Conv2D(64, (2, 2), padding='same', activation='relu')(conc)
    conc = MaxPooling2D(pool_size =(2, 2))(conc)
    conc = Flatten()(conc)
    
    out = Dense(64, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0

def createModel_08_16_32_64():
    
    from keras.layers import concatenate
    from keras import backend as K
    K.set_image_data_format('channels_first')
    #K.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=28,data_format='channels_first')(input0) #8*8
    model2 = Cropping2D(cropping=24,data_format='channels_first')(input0) #16*16
    model3 = Cropping2D(cropping=16,data_format='channels_first')(input0) #32*32
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model3 = MaxPooling2D(pool_size =(4, 4))(model3)
    model4 = MaxPooling2D(pool_size =(8, 8))(input0)
    conc = concatenate([model1, model2, model3, model4], axis=1)
    
    conc = Conv2D(64, (3, 3), padding='same', activation='relu')(conc)
    conc = Conv2D(64, (3, 3), padding='same', activation='relu')(conc)
    conc = MaxPooling2D(pool_size =(2, 2))(conc)
    conc = Conv2D(96, (2, 2), padding='same', activation='relu')(conc)
    conc = Conv2D(96, (2, 2), padding='same', activation='relu')(conc)
    conc = MaxPooling2D(pool_size =(2, 2))(conc)
    conc = Flatten()(conc)
    
    out = Dense(128, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0

    
def createModel_08_32_64():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=28,data_format='channels_first')(input0) #8*8
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(24, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    
    model3 = Cropping2D(cropping=16,data_format='channels_first')(input0) #32*32
    model3 = Conv2D(8, (5, 5), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(36, (3, 3), padding='same', activation='relu')(model3)
    model3 = Conv2D(36, (3, 3), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(64, (2, 2), padding='same', activation='relu')(model3)
    model3 = Conv2D(64, (2, 2), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(96, (2, 2), padding='same', activation='relu')(model3)
    model3 = Conv2D(96, (2, 2), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Flatten()(model3)
    
    model2 = Conv2D(18, (5, 5), activation='relu')(input0) #60*60
    model2 = MaxPooling2D(pool_size =(3, 3))(model2)
    model2 = Conv2D(36, (4, 4), padding='same', activation='relu')(model2)
    model2 = Conv2D(36, (4, 4), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(96, (2, 2), padding='same', activation='relu')(model2)
    model2 = Conv2D(96, (2, 2), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Flatten()(model2)
    
    conc = Concatenate()([model1, model2, model3])
    out = Dense(128, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0


def createModel_08_16_32_60():
    
    keras.backend.set_image_dim_ordering('th')
    
    input0 = Input(shape=(3, 64, 64))
    
    model1 = Cropping2D(cropping=28,data_format='channels_first')(input0) #8*8
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = Conv2D(18, (3, 3), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Conv2D(24, (2, 2), padding='same', activation='relu')(model1)
    model1 = Conv2D(36, (2, 2), padding='same', activation='relu')(model1)
    model1 = MaxPooling2D(pool_size =(2, 2))(model1)
    model1 = Flatten()(model1)
    
    model4 = Cropping2D(cropping=24,data_format='channels_first')(input0) #16*16
    model4 = Conv2D(8, (5, 5), padding='same', activation='relu')(model4)
    model4 = MaxPooling2D(pool_size =(2, 2))(model4)
    model4 = Conv2D(36, (3, 3), padding='same', activation='relu')(model4)
    model4 = Conv2D(36, (3, 3), padding='same', activation='relu')(model4)
    model4 = MaxPooling2D(pool_size =(2, 2))(model4)
    model4 = Conv2D(64, (2, 2), padding='same', activation='relu')(model4)
    model4 = Conv2D(64, (2, 2), padding='same', activation='relu')(model4)
    model4 = MaxPooling2D(pool_size =(2, 2))(model4)
    model4 = Flatten()(model4)
    
    model3 = Cropping2D(cropping=16,data_format='channels_first')(input0) #32*32
    model3 = Conv2D(8, (5, 5), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(36, (3, 3), padding='same', activation='relu')(model3)
    model3 = Conv2D(36, (3, 3), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(64, (2, 2), padding='same', activation='relu')(model3)
    model3 = Conv2D(64, (2, 2), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Conv2D(96, (2, 2), padding='same', activation='relu')(model3)
    model3 = Conv2D(96, (2, 2), padding='same', activation='relu')(model3)
    model3 = MaxPooling2D(pool_size =(2, 2))(model3)
    model3 = Flatten()(model3)
    
    model2 = Conv2D(18, (5, 5), activation='relu')(input0) #60*60
    model2 = MaxPooling2D(pool_size =(3, 3))(model2)
    model2 = Conv2D(36, (4, 4), padding='same', activation='relu')(model2)
    model2 = Conv2D(36, (4, 4), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = Conv2D(64, (3, 3), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Conv2D(96, (2, 2), padding='same', activation='relu')(model2)
    model2 = Conv2D(96, (2, 2), padding='same', activation='relu')(model2)
    model2 = MaxPooling2D(pool_size =(2, 2))(model2)
    model2 = Flatten()(model2)
    
    conc = Concatenate()([model1, model2, model3])
    out = Dense(128, activation='relu')(conc)
    out = Dense(64, activation='relu')(out)
    out = Dropout(0.5)(out)
    out = Dense(2, activation='softmax')(out)
    
    model0 = Model(inputs=input0, outputs=out)
        
    return model0