# -*- coding: utf-8 -*-
import numpy as np
import os

def RFFeature():
    
    srcPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190812/fit2'
    featureFile = 'features2.npz'
    
    tdata = np.load("%s/%s"%(srcPath, featureFile))
    features=tdata['features']
    labels=tdata['labels'].astype(int)
    fnames=tdata['fnames']
    
    features=np.array(features)
    labels=np.array(labels).astype(int)
    fnames=np.array(fnames)
    print(features.shape)
    
    tfeatures=features[labels==1]
    tlabels=labels[labels==1]
    tfnames=fnames[labels==1]
    ffeatures=features[labels==0]
    flabels=labels[labels==0]
    ffnames=fnames[labels==0]
    
    print(tfeatures.shape)
    print(ffeatures.shape)
    
    N_data = 1900
    
    tfeatures=tfeatures[:N_data]
    tlabels=tlabels[:N_data]
    tfnames=tfnames[:N_data]
    ffeatures=ffeatures[:N_data]
    flabels=flabels[:N_data]
    ffnames=ffnames[:N_data]
    
    allfeatures = np.concatenate([tfeatures, ffeatures])
    alllabels = np.concatenate([tlabels, flabels])
    allfnames = np.concatenate([tfnames, ffnames])
    print(allfeatures.shape)
    print(alllabels.shape)
    print(allfnames.shape)
    
    XY = []
    for i in range(allfeatures.shape[0]):
        XY.append((allfeatures[i],alllabels[i],allfnames[i]))
    XY = np.array(XY)
    np.random.shuffle(XY)
    
    X = []
    Y = []
    Z = []
    for i in range(XY.shape[0]):
        X.append(XY[i][0])
        Y.append(XY[i][1])
        Z.append(XY[i][2])
    X = np.array(X)
    Y = np.array(Y)
    Z = np.array(Z)
    
    destPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190815'
    featureFile = 'features_test.npz'
    if not os.path.exists(destPath):
        os.makedirs(destPath)
    np.savez_compressed("%s/%s"%(destPath,featureFile), features=X, labels=Y, fnames=Z)

def getImages1():
    
    #tpath1 = '/home/xy/Downloads/myresource/deep_data2/simot/train_20190122/SIM_TOT_REAL_FOT_bin_none_64_fot10w_20190122.npz'
    tpath1 = '/home/xy/Downloads/myresource/deep_data2/simot/train_20190122/FINAL_TEST_ADD_REAL_DATA_bin_none.npz'
    print("%s"%(tpath1))
    tdata1 = np.load(tpath1)
    X = tdata1['X']
    Y = tdata1['Y']
    s2n = tdata1['s2n']
    
    srcPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190815'
    featureFile = 'features_test.npz'
    tdata = np.load("%s/%s"%(srcPath, featureFile))
    features=tdata['features']
    labels=tdata['labels']
    fnames=tdata['fnames']
    print(features[:5])
    print(labels[:5])
    print(fnames[:5])
    
    X1 = []
    Y1 = []
    s2n1 = []
    for i in range(fnames.shape[0]):
        tname = fnames[i] #t0000001obj.fit
        tidx = int(tname[1:8])
        X1.append(X[tidx])
        Y1.append(Y[tidx])
        s2n1.append(s2n[tidx])
    
    X1 = np.array(X1)
    Y1 = np.array(Y1)
    s2n1 = np.array(s2n1)
    print(X1.shape)
    print(Y1.shape)
    print(s2n1.shape)
    
    destPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190815'
    featureFile = 'test_imgs_3_64_2.npz'
    if not os.path.exists(destPath):
        os.makedirs(destPath)
    np.savez_compressed("%s/%s"%(destPath,featureFile), X=X1, Y=Y1, s2n=s2n1)
    
def getImages2():
    
    tpath1 = '/home/xy/Downloads/myresource/deep_data2/simot/img20190815/test_imgs_3_64_2.npz'
    print("%s"%(tpath1))
    tdata1 = np.load(tpath1)
    X = tdata1['X']
    Y = tdata1['Y']
    s2n = tdata1['s2n']
    print(X.shape)
    print(Y.shape)
    print(s2n.shape)
    #return
    
    X = X[:,:,16:48,16:48]
    X1 = np.rot90(X, 1, (2,3))
    X2 = np.rot90(X1, 1, (2,3))
    X3 = np.rot90(X2, 1, (2,3))

    print(X1.shape)
    print(X2.shape)
    print(X3.shape)
    print(Y.shape)
    print(s2n.shape)
    
    destPath = '/home/xy/Downloads/myresource/deep_data2/simot/img20190815'
    featureFile = 'test_imgs_4_3_64.npz'
    if not os.path.exists(destPath):
        os.makedirs(destPath)
    np.savez_compressed("%s/%s"%(destPath,featureFile), X0=X, X1=X1, X2=X2, X3=X3, Y=Y, s2n=s2n)
    
if __name__ == "__main__":
    
    #RFFeature()
    #getImages1()
    getImages2()