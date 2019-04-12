# -*- coding: utf-8 -*-
import numpy as np
import os
import keras
from keras import backend as K
from keras.models import load_model
    
                
def doAll():
    
    #dateStr = datetime.strftime(datetime.now(), "%Y%m%d")
    dateStr = '20190403'
    workPath = "/home/xy/Downloads/myresource/deep_data2/simot/train_%s"%(dateStr)
    if not os.path.exists(workPath):
        os.system("mkdir %s"%(workPath))
    print("work path is %s"%(workPath))
    
    tModelNamePart1 = 'model_80w_20190403_branch3_train12'
    data1 = 'test'
    data2 = 'refine1_allMisMatch'
    
    test(workPath, tModelNamePart1, data1)
    test(workPath, tModelNamePart1, data2)
   

def test(workPath, tModelNamePart, dataName):
        
    dataPath1 = "%s/data/%s.npz"%(workPath, dataName)
    tdata = np.load(dataPath1)
    X_test = tdata['X']
    Y_test = tdata['Y']
    s2n_test = tdata['s2n']
    print(X_test.shape)
    print(Y_test.shape)
    print(s2n_test.shape)
    
    K.set_image_data_format('channels_first')
    for i in range(8):
        
        modelName = "%s_%d9.h5"%(tModelNamePart, i)
        model = load_model("%s/%s"%(workPath, modelName))
        #model = load_model("%s/%s"%(workPath, modelName),custom_objects={'concatenate':keras.layers.concatenate})
        Y_pred = model.predict(X_test)
        pbb_threshold = 0.5
        pred_labels = np.array((Y_pred[:, 1] > pbb_threshold), dtype = "int")

        TIdx = Y_test[:, 1]==1
        FIdx = Y_test[:, 1]==0
        T_pred_rst = pred_labels[TIdx]
        F_pred_rst = pred_labels[FIdx]
        
        TP = ((T_pred_rst == 1).astype(int)).sum()
        TN = ((F_pred_rst == 0).astype(int)).sum()
        FP = ((F_pred_rst == 1).astype(int)).sum()
        FN = ((T_pred_rst == 0).astype(int)).sum()
        
        accuracy = (TP+TN)*1.0/(TP+FN+TN+FP)
        precision = (TP)*1.0/(TP+FP)
        recall = (TP)*1.0/(TP+FN)
        f1_score = 2.0*(precision*recall)/(precision+recall)
        
        print("%s, Correctly classified %d out of %d, TP=%d,TN=%d,FP=%d,FN=%d, accuracy=%f%%, precision=%f%%, recall=%f%%, f1_score=%f%%"%
              (modelName, (pred_labels == Y_test[:, 1].astype(int)).sum(), Y_test.shape[0],
              TP, TN, FP, FN,
              accuracy*100,precision*100,recall*100,f1_score*100))

    
if __name__ == "__main__":
    
    doAll()



