# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage
import math
from PIL import Image

def zscale_image(input_img, contrast=0.25):

    """This emulates ds9's zscale feature. Returns the suggested minimum and
    maximum values to display."""
    
    #samples = input_img.flatten()
    samples = input_img[input_img>0]
    samples = samples[~np.isnan(samples)]
    samples.sort()
    chop_size = int(0.1*len(samples))
    subset = samples[chop_size:-chop_size]
    
    if len(subset)<10:
        return np.array([])

    i_midpoint = int(len(subset)/2)
    I_mid = subset[i_midpoint]

    fit = np.polyfit(np.arange(len(subset)) - i_midpoint, subset, 1)
    # fit = [ slope, intercept]

    z1 = I_mid + fit[0]/contrast * (1-i_midpoint)/1.0
    z2 = I_mid + fit[0]/contrast * (len(subset)-i_midpoint)/1.0
    zmin = z1
    zmax = z2
    
    if zmin<0:
        zmin=0
    if math.fabs(zmin-zmax)<0.000001:
        zmin = np.min(samples)
        zmax = np.max(samples)
    
    zimg = input_img.copy()
    zimg[zimg>zmax] = zmax
    zimg[zimg<zmin] = zmin
    zimg=(((zimg-zmin)/(zmax-zmin))*255).astype(np.uint8)
    
    return zimg
    
def draw(tpath):
    
    tdata1 = np.load(tpath)
    imgs = tdata1['imgs']
    X = imgs
    tobjImg = zscale_image(X[0])
    tTempImg = zscale_image(X[1])
    tResiImg = zscale_image(X[2])
    
    padding2 = 1
    startX2 = 46-padding2
    endX2 = 54-padding2
    tobjImg2 = tobjImg[startX2:endX2,startX2:endX2]
    tTempImg2 = tTempImg[startX2:endX2,startX2:endX2]
    tResiImg2 = tResiImg[startX2:endX2,startX2:endX2]
    print(tResiImg2.shape)
    
    padding = 1
    startX = 18-padding
    endX = 82-padding
    tobjImg = tobjImg[startX:endX,startX:endX]
    tTempImg = tTempImg[startX:endX,startX:endX]
    tResiImg = tResiImg[startX:endX,startX:endX]
    print(tResiImg.shape)
    
    plt.clf()
    fig, axes = plt.subplots(1, 3, figsize=(6, 2))
    print("%.2f,%.2f,%.2f"%(np.mean(X[0]),np.mean(X[1]),np.mean(X[2])))
    axes.flat[0].imshow(tobjImg, interpolation = "nearest", cmap='gray')
    axes.flat[1].imshow(tTempImg, interpolation = "nearest", cmap='gray')
    axes.flat[2].imshow(tResiImg, interpolation = "nearest", cmap='gray')
    #axes.flat[0].set_title ("object")
    #axes.flat[1].set_title ("template")
    #axes.flat[2].set_title ("residual")
    axes.flat[0].set_xticks([])
    axes.flat[0].set_yticks([])
    axes.flat[1].set_xticks([])
    axes.flat[1].set_yticks([])
    axes.flat[2].set_xticks([])
    axes.flat[2].set_yticks([])
    plt.tight_layout()
    plt.subplots_adjust(wspace =0.02, hspace =0)
    #plt.show()
    plt.savefig("%s_full64.png"%(tpath[:-4]))

    '''  '''
    tzoom = 0.5
    tobjImg1 = scipy.ndimage.zoom(tobjImg, tzoom, order=0)
    tTempImg1 = scipy.ndimage.zoom(tTempImg, tzoom, order=0)
    tResiImg1 = scipy.ndimage.zoom(tResiImg, tzoom, order=0)
    plt.clf()
    fig, axes = plt.subplots(1, 3, figsize=(4, 2))
    axes.flat[0].imshow(tobjImg1, interpolation = "nearest", cmap='gray')
    axes.flat[1].imshow(tTempImg1, interpolation = "nearest", cmap='gray')
    axes.flat[2].imshow(tResiImg1, interpolation = "nearest", cmap='gray')
    #axes.flat[0].set_title ("object")
    #axes.flat[1].set_title ("template")
    #axes.flat[2].set_title ("residual")
    axes.flat[0].set_xticks([])
    axes.flat[0].set_yticks([])
    axes.flat[1].set_xticks([])
    axes.flat[1].set_yticks([])
    axes.flat[2].set_xticks([])
    axes.flat[2].set_yticks([])
    plt.tight_layout()
    plt.subplots_adjust(wspace =0.02, hspace =0)
    #plt.show()
    plt.savefig("%s_zoom32.png"%(tpath[:-4]))
    
    plt.clf()
    fig, axes = plt.subplots(1, 3, figsize=(3, 2))
    axes.flat[0].imshow(tobjImg2, interpolation = "nearest", cmap='gray')
    axes.flat[1].imshow(tTempImg2, interpolation = "nearest", cmap='gray')
    axes.flat[2].imshow(tResiImg2, interpolation = "nearest", cmap='gray')
    #axes.flat[0].set_title ("object")
    #axes.flat[1].set_title ("template")
    #axes.flat[2].set_title ("residual")
    axes.flat[0].set_xticks([])
    axes.flat[0].set_yticks([])
    axes.flat[1].set_xticks([])
    axes.flat[1].set_yticks([])
    axes.flat[2].set_xticks([])
    axes.flat[2].set_yticks([])
    plt.tight_layout()
    plt.subplots_adjust(wspace =0.03, hspace =0)
    #plt.show()
    plt.savefig("%s_center8.png"%(tpath[:-4]))

def draw2(tpath):
    
    tdata1 = np.load(tpath)
    imgs = tdata1['imgs']
    X = imgs
    tobjImg = zscale_image(X[0])
    tTempImg = zscale_image(X[1])
    tResiImg = zscale_image(X[2])
    
    padding2 = 1
    #startX2 = 46-padding2
    #endX2 = 54-padding2
    startX2 = 44-padding2
    endX2 = 56-padding2
    tobjImg2 = tobjImg[startX2:endX2,startX2:endX2]
    tTempImg2 = tTempImg[startX2:endX2,startX2:endX2]
    tResiImg2 = tResiImg[startX2:endX2,startX2:endX2]
    print(tResiImg2.shape)
    
    padding = 1
    startX = 18-padding
    endX = 82-padding
    tobjImg = tobjImg[startX:endX,startX:endX]
    tTempImg = tTempImg[startX:endX,startX:endX]
    tResiImg = tResiImg[startX:endX,startX:endX]
    print(tResiImg.shape)
    
    tzoom = 0.5
    tobjImg1 = scipy.ndimage.zoom(tobjImg, tzoom, order=0)
    tTempImg1 = scipy.ndimage.zoom(tTempImg, tzoom, order=0)
    tResiImg1 = scipy.ndimage.zoom(tResiImg, tzoom, order=0)
    
    tzoom = 4
    tobjImg = scipy.ndimage.zoom(tobjImg, tzoom, order=0)
    tTempImg = scipy.ndimage.zoom(tTempImg, tzoom, order=0)
    tResiImg = scipy.ndimage.zoom(tResiImg, tzoom, order=0)
    xspace = np.ones((tobjImg.shape[0],10), np.uint8)*255
    timg = np.concatenate((tobjImg, xspace, tTempImg, xspace, tResiImg), axis=1)
    Image.fromarray(timg).save("%s_full64.png"%(tpath[:-4]))
    
    tzoom = 4
    tobjImg1 = scipy.ndimage.zoom(tobjImg1, tzoom, order=0)
    tTempImg1 = scipy.ndimage.zoom(tTempImg1, tzoom, order=0)
    tResiImg1 = scipy.ndimage.zoom(tResiImg1, tzoom, order=0)
    xspace = np.ones((tobjImg1.shape[0],6), np.uint8)*255
    timg = np.concatenate((tobjImg1, xspace, tTempImg1, xspace, tResiImg1), axis=1)
    Image.fromarray(timg).save("%s_zoom32.png"%(tpath[:-4]))
    
    tzoom = 14
    tobjImg2 = scipy.ndimage.zoom(tobjImg2, tzoom, order=0)
    tTempImg2 = scipy.ndimage.zoom(tTempImg2, tzoom, order=0)
    tResiImg2 = scipy.ndimage.zoom(tResiImg2, tzoom, order=0)
    xspace = np.ones((tobjImg2.shape[0],6), np.uint8)*255
    timg = np.concatenate((tobjImg2, xspace, tTempImg2, xspace, tResiImg2), axis=1)
    Image.fromarray(timg).save("%s_center8.png"%(tpath[:-4]))
    
if __name__ == "__main__":
    
    tpath1 = "image/bad_sample190121.npz"
    tpath2 = "image/tot_sample190121.npz"
    tpath3 = "image/fot_sample190121.npz"
    tpath4 = "image/bad_sample190131.npz"
    
    #draw2(tpath1)
    #draw2(tpath2)
    #draw2(tpath3)
    draw2(tpath4)