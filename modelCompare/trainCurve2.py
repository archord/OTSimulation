# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage
import math
from PIL import Image
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA

def draw(tpath, minX=10):
    
    tdata = np.loadtxt(tpath, delimiter=',')
    
    trainLoss = tdata[:,0]
    validLoss = tdata[:,1]
    validLoss = 1-validLoss
    X = np.linspace(1,trainLoss.shape[0]+1, 100)
    xticks = np.linspace(10,trainLoss.shape[0], 10)
    print(X.shape)
    print(trainLoss.shape)
    
    fig = plt.figure(1, figsize=(4, 2))
    host = host_subplot(111, axes_class=AA.Axes)
    #plt.subplots_adjust(right=0.75)
    par1 = host.twinx()
    host.set_xticks(xticks)
    
    p1, = host.plot(X[minX:], trainLoss[minX:],'-r',label="train loss")
    p2, = par1.plot(X[minX:], validLoss[minX:],'-b',label="verify accuracy")
    
    #host.set_ylabel("train loss")
    #par1.set_ylabel("validation accuracy")
    #host.set_xlabel('train epochs')
    host.set_xlim(minX-3, 100)
    par1.set_xlim(minX-3, 100)
    host.grid()
    #host.legend(loc = 'center right', prop={'size':10})
    plt.subplots_adjust(left=0.15, right=0.85, top=0.95, bottom=0.1)
    #plt.title('model 2')
    plt.show()
    #fig.savefig('test082-2.png')

def draw2(tpath, title, minX=10):
    
    tdata = np.loadtxt(tpath, delimiter=',')
    
    trainLoss = tdata[:,0]
    validLoss = tdata[:,1]
    #validLoss = 1-validLoss
    X = np.linspace(1,trainLoss.shape[0]+1, 100)
    xticks = np.linspace(0,trainLoss.shape[0], 11)
    print(X.shape)
    print(trainLoss.shape)
    
    fig = plt.figure(1, figsize=(10, 6))
    
    left, bottom, width, height = 0.1,0.1,0.8,0.8
    host = fig.add_axes([left,bottom,width,height])
    host.plot(X, trainLoss,'-r',label="train")
    host.plot(X, validLoss,'-b',label="validation")
    host.set_ylabel("loss", {'size': 12})
    host.set_xlabel('train epochs', {'size': 12})
    host.set_xlim(0, 100)
    host.set_xticks(xticks)
    host.grid()
    #host.legend(loc = 'upper right')
    host.legend(loc = 'upper right', prop={'size':12})
    plt.subplots_adjust(left=0.15, right=0.85, top=0.9, bottom=0.15)
    plt.title(title)
    
    
    left, bottom, width, height = 0.3,0.25,0.5,0.5
    ax2 = fig.add_axes([left,bottom,width,height])
    ax2.plot(X[minX:], trainLoss[minX:],'-r')
    ax2.plot(X[minX:], validLoss[minX:],'-b')
    ax2.set_xticks(xticks)
    ax2.set_xlim(minX-3, 100)
    ax2.grid()
    
    #plt.tight_layout()
    #plt.show()
    #fig.savefig('test641.png')
    plt.savefig('%s.svg'%(title),dpi=600,format='svg')


if __name__ == "__main__":
    
    tpath1 = "data/model_08_16_32_60_2.txt"
    tpath2 = "data/modelHits2.txt"
    
    title='Ours'
    draw2(tpath1, title, 10)
    title='Deep-HiTS'
    draw2(tpath2, title, 10)