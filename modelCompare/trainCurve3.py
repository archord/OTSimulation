# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage
import math
from PIL import Image
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA


def draw(minX=10):
    
    tpath1 = "data/model_08_16_32_60_2.txt"
    tpath2 = "data/modelHits2.txt"
    title='two_compare'
    
    tdata1 = np.loadtxt(tpath1, delimiter=',')
    tdata2 = np.loadtxt(tpath2, delimiter=',')
    
    trainLoss = tdata1[:,0]
    validLoss = tdata1[:,1]
    trainLoss2 = tdata2[:,0]
    validLoss2 = tdata2[:,1]
    #validLoss = 1-validLoss
    X = np.linspace(1,trainLoss.shape[0]+1, 100)
    xticks = np.linspace(0,trainLoss.shape[0], 11)
    print(X.shape)
    print(trainLoss.shape)
    
    fig = plt.figure(1, figsize=(8, 5))
    
    left, bottom, width, height = 0.14,0.1,0.84,0.86
    host = fig.add_axes([left,bottom,width,height])
    host.plot(X, trainLoss,'r', label="MSCNN training")
    host.plot(X, validLoss,'--g', label="MSCNN validation")
    host.plot(X, trainLoss2,':b', label="RICNN training")
    host.plot(X, validLoss2,'-.m',label="RICNN validation")
    host.set_ylabel("error", {'size': 14})
    host.set_xlabel('train epochs', {'size': 14})
    host.set_xlim(0, 100)
    host.set_xticks(xticks)
    host.grid()
    #host.legend(loc = 'upper right')
    host.legend(loc = 'upper right', prop={'size':12})
    #plt.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)
    #plt.title(title)
    
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    
    left, bottom, width, height = 0.25,0.4,0.4,0.5
    ax2 = fig.add_axes([left,bottom,width,height])
    ax2.plot(X[minX:], trainLoss[minX:],'r')
    ax2.plot(X[minX:], validLoss[minX:],'--g')
    ax2.plot(X[minX:], trainLoss2[minX:],':b')
    ax2.plot(X[minX:], validLoss2[minX:],'-.m')
    ax2.set_xticks(xticks)
    ax2.set_xlim(minX-3, 100)
    ax2.grid()
    
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    
    #plt.tight_layout()
    #plt.show()
    #fig.savefig('test641.png')
    plt.savefig('%s.svg'%(title),dpi=600,format='svg')


if __name__ == "__main__":
        
    draw(20)