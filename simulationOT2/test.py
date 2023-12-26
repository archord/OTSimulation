# -*- coding: utf-8 -*-

from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.utils.vis_utils import plot_model
from keras.utils.vis_utils import model_to_dot
import keras
from keras.models import load_model

keras.backend.set_image_dim_ordering('th')

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

optimizer = keras.optimizers.Adam(lr=0.0001, beta_1=0.9, beta_2=0.999,decay=0.0)
model.compile(loss='mean_squared_error', optimizer=optimizer)

X_train = X
Y_train = Y
model.fit(X_train, Y_train, batch_size=32, nb_epoch=5, validation_split=0.2)
#model.save_weights("/home/xy/Downloads/myresource/deep_data2/simot/train_model/m0907.h5")
model.save("/home/xy/Downloads/myresource/deep_data2/simot/train_model/m0907.h5")


model = load_model('/home/xy/Downloads/myresource/deep_data2/simot/train_model/m0907.h5')
preY = model.predict(X)


