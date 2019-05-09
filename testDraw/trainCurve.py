# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage
import math
from PIL import Image
from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA

def draw(tpath):
    
    tdata = np.loadtxt(tpath)
    
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
    
    p1, = host.plot(X[10:], trainLoss[10:],'.-r',label="train loss")
    p2, = par1.plot(X[10:], validLoss[10:],'*-b',label="verify accuracy")
    
    #host.set_ylabel("train loss")
    #par1.set_ylabel("validation accuracy")
    #host.set_xlabel('train epochs')
    host.set_xlim(10, 100)
    par1.set_xlim(10, 100)
    host.set_xticks(xticks)
    host.grid()
    host.legend(loc = 'center right', prop={'size':10})
    plt.subplots_adjust(left=0.15, right=0.85, top=0.95, bottom=0.1)
    #plt.title('model 2')
    #plt.show()
    fig.savefig('test082-2.png')

def draw2(tpath):
    
    tdata = np.loadtxt(tpath)
    
    trainLoss = tdata[:,0]
    validLoss = tdata[:,1]
    validLoss = 1-validLoss
    X = np.linspace(1,trainLoss.shape[0]+1, 100)
    xticks = np.linspace(0,trainLoss.shape[0], 11)
    print(X.shape)
    print(trainLoss.shape)
    
    fig = plt.figure(1, figsize=(5, 3))
    host = host_subplot(111, axes_class=AA.Axes)
    #plt.subplots_adjust(right=0.75)
    par1 = host.twinx()
    
    p1, = host.plot(X, trainLoss,'.-r',label="train loss")
    p2, = par1.plot(X, validLoss,'*-b',label="validation accuracy")
    
    host.set_ylabel("train loss")
    par1.set_ylabel("validation accuracy")
    host.set_xlabel('train epochs')
    host.set_xlim(0, 100)
    host.set_xticks(xticks)
    host.grid()
    host.legend(loc = 'center right')
    plt.subplots_adjust(left=0.15, right=0.85, top=0.9, bottom=0.15)
    plt.title('model 2')
    #plt.show()
    fig.savefig('test641.png')
    
def draw3():
    
    host = host_subplot(111, axes_class=AA.Axes)
    plt.subplots_adjust(right=0.75)
    
    par1 = host.twinx()
    par2 = host.twinx()
    
    offset = 100
    new_fixed_axis = par2.get_grid_helper().new_fixed_axis
    par2.axis["right"] = new_fixed_axis(loc="right",
                                        axes=par2,
                                        offset=(offset, 0))
    
    par1.axis["right"].toggle(all=True)
    par2.axis["right"].toggle(all=True)
    
    host.set_xlim(0, 2)
    host.set_ylim(0, 2)
    
    host.set_xlabel("Distance")
    host.set_ylabel("Density")
    par1.set_ylabel("Temperature")
    par2.set_ylabel("Velocity")
    
    p1, = host.plot([0, 1, 2], [0, 1, 2], label="Density")
    p2, = par1.plot([0, 1, 2], [0, 3, 2], label="Temperature")
    p3, = par2.plot([0, 1, 2], [50, 30, 15], label="Velocity")
    
    par1.set_ylim(0, 4)
    par2.set_ylim(1, 65)
    
    host.legend()
    
    host.axis["left"].label.set_color(p1.get_color())
    par1.axis["right"].label.set_color(p2.get_color())
    par2.axis["right"].label.set_color(p3.get_color())
    
    plt.draw()
    plt.show()



if __name__ == "__main__":
    
    tpath1 = "data/train8.log"
    tpath2 = "data/train64.log"
    
    draw(tpath1)
    
    #draw2()