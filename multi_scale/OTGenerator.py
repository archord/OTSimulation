# -*- coding: utf-8 -*-

import keras
import math
import os
import numpy as np
from keras.models import Sequential
from keras.layers import Dense


class OTGenerator(keras.utils.Sequence):

    def __init__(self, dataPath, batch_size=128, shuffle=True):
        self.batch_size = batch_size
        self.dataPath = dataPath
        self.curDataBlock=np.array([])

    def __len__(self):
        #计算每一个epoch的迭代次数 944376, 800000
        return math.ceil(800000 / float(self.batch_size))

    def __getitem__(self, index):
        
        X, y = self.data_generation(index)

        return X, y

    def data_generation(self, index):
        
        
        startIdx = index*self.batch_size
        endIdx = (index+1)*self.batch_size
        fileStartIdx = math.floor(startIdx/100000)+1
        fileEndIdx = math.floor(endIdx/100000)+1
                
        tpath = '%s/train%d.npz'%(self.dataPath, fileEndIdx)
        if self.curDataBlock.shape[0]==0:
            self.curDataBlock = np.load(tpath)
            
        if fileStartIdx==fileEndIdx:
            X = self.curDataBlock['X'][startIdx:endIdx]
            Y = self.curDataBlock['Y'][startIdx:endIdx]
        else:
            lastDataBlock = self.curDataBlock
            self.curDataBlock = np.load(tpath)
            X1 = lastDataBlock['X'][startIdx:]
            Y1 = lastDataBlock['Y'][startIdx:]
            X2 = self.curDataBlock['X'][:endIdx]
            Y2 = self.curDataBlock['Y'][:endIdx]
            
            X = np.concatenate((X1,X2), axis=0)
            Y = np.concatenate((Y1,Y2), axis=0)
            
        return X, Y

