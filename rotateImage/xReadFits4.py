import sys
# author: xlp
# at 20230117,
from astropy.io import fits as pyfits
from astropy.visualization.interval import ZScaleInterval
from skimage import data, exposure, img_as_float
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from astropy.visualization import simple_norm
# import Image,ImageFont,ImageDraw
import skimage as image
from pylab import *
import numpy as np
#import PIL.Image as pil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
#import cv2
from scipy import interpolate
from scipy import optimize
from math import pi
import math


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

def filterArray(img):

    timg = Image.fromarray(img)
    timg2 = timg.filter(ImageFilter.GaussianBlur(radius= 5)) 
    # timg2 = timg.filter(ImageFilter.MedianFilter(size= 19)) 
    return np.array(timg2)

def extendImg(img):

    oldImg = np.array(img)
    h, w, c = oldImg.shape
    maxSize = math.ceil(math.sqrt(w*w+h*h))
    newImg = np.zeros((maxSize, maxSize, c), dtype=np.uint8)
    # print(w,h,maxSize)
    
    x0 = math.ceil((maxSize-w)/2)
    y0 = math.ceil((maxSize-h)/2)
    # print(x0,y0)
    
    #补充上边
    # tpadd = oldImg[0:5,:]
    # tpadd = np.mean(tpadd, axis=0)
    # print(tpadd.shape)
    newImg[0:y0,x0:x0+w]=oldImg[5,:]
    # newImg[0:y0,x0:x0+w]=tpadd
    newImg[0:y0,x0:x0+w]=filterArray(newImg[0:y0,x0:x0+w])
    
    #补充下边
    newImg[y0+h:,x0:x0+w]=oldImg[-1,:]
    newImg[y0+h:,x0:x0+w]=filterArray(newImg[y0+h:,x0:x0+w])

    #补充左边
    tarr =np.repeat(oldImg[:, np.newaxis, 0], x0, axis=1)
    # newImg[y0:y0+h,0:x0]=oldImg[:,0]
    newImg[y0:y0+h,0:x0]=tarr
    newImg[y0:y0+h,0:x0]=filterArray(newImg[y0:y0+h,0:x0])

    #补充右边
    tarr =np.repeat(oldImg[:, np.newaxis, -1], maxSize-(x0+w), axis=1)
    # newImg[y0:y0+h,x0:x0+w]=oldImg[:,-1]
    newImg[y0:y0+h,x0+w:]=tarr
    newImg[y0:y0+h,x0+w:]=filterArray(newImg[y0:y0+h,x0+w:])

    #填充中间
    newImg[y0:y0+h,x0:x0+w]=oldImg

    return Image.fromarray(newImg)

def rotateImg(imgArray, rotateAngle):
    
    img = Image.fromarray(imgArray)
    img = img.convert('RGB')
    w,h = img.size
    newImg = extendImg(img)

    # rotateAngle=210  #degree
    fillcolor = (255,255,255)
    rotImg = newImg.rotate(rotateAngle, expand=1, fillcolor=fillcolor)
    newW, newH = rotImg.size
    # rotImg = np.array(rotImg)
    # sub2=rotImg[(newH-h)//2:(newH-h)//2+h, (newW-w)//2:(newW-w)//2+w]
    # Image.fromarray(sub2, 'RGBA').save("%s_rotate_%d.png"%(imgPath.split(".")[0], rotateAngle))
    cropImg = rotImg.crop(((newW-w)//2,(newH-h)//2, (newW-w)//2+w,(newH-h)//2+h))
    return np.array(cropImg)

def r(x, y, xc, yc):
    return np.sqrt((x-xc)**2 + (y-yc)**2)


def f(c, x, y):
    Ri = r(x, y, *c)
    return np.square(Ri - Ri.mean())

def least_squares_circle(coords):
    """
    Circle fit using least-squares solver.
    Inputs:

        - coords, list or numpy array with len>2 of the form:
        [
    [x_coord, y_coord],
    ...,
    [x_coord, y_coord]
    ]
        or numpy array of shape (n, 2)

    Outputs:

        - xc : x-coordinate of solution center (float)
        - yc : y-coordinate of solution center (float)
        - R : Radius of solution (float)
        - residu : MSE of solution against training data (float)
    """

    x, y = None, None
    if isinstance(coords, np.ndarray):
        x = coords[:, 0]
        y = coords[:, 1]
    elif isinstance(coords, list):
        x = np.array([point[0] for point in coords])
        y = np.array([point[1] for point in coords])
    else:
        raise Exception("Parameter 'coords' is an unsupported type: " + str(type(coords)))

    # coordinates of the barycenter
    x_m = np.mean(x)
    y_m = np.mean(y)
    center_estimate = x_m, y_m
    center, _ = optimize.leastsq(f, center_estimate, args=(x, y))
    xc, yc = center
    Ri       = r(x, y, *center)
    R        = Ri.mean()
    residu   = np.sum((Ri - R)**2)
    return xc, yc, R, residu



def circle_points(RN, center, radius):
    radians = np.linspace(0, 2 * np.pi, RN)
    print("============")
    print(center[1])
    print(center[0])
    c = center[1] + radius * np.cos(radians)  # polar co-ordinates
    r = center[0] + radius * np.sin(radians)
    #print(np.array([c, r]).T)
    return np.array([c, r]).T

def mark_ele_40deg(filename):
    xc, yc = [],[]
    for line in open(filename, 'r'):
        values = [s for s in line.split()]
        xc.append(float(values[6]))
        yc.append(float(values[7]))

    #print(f'{xc}    {yc}')
    return xc, yc


def change_size_data(binary_image):

    print(binary_image.shape)
    x = binary_image.shape[0]
    print("height y=", x)
    y = binary_image.shape[1]
    print("width x=", y)
    edges_x = []
    edges_y = []
    for i in range(x):
        for j in range(y):
            #print(binary_image[i][j])
            if binary_image[i][j].any() == 255:
                edges_x.append(i)
                edges_y.append(j)

    left = min(edges_x)  # 左边界
    right = max(edges_x)  # 右边界
    width = right - left  # 宽度
    bottom = min(edges_y)  # 底部
    top = max(edges_y)  # 顶部
    height = top - bottom  # 高度

    pre1_picture = image[left:left + width, bottom:bottom + height]  # 图片截取
    return pre1_picture  # 返回图片数据


def plot_data_circle(x, y, xc, yc, R):
    """
    Plot data and a fitted circle.
    Inputs:

        x : data, x values (array)
        y : data, y values (array)
        xc : fit circle center (x-value) (float)
        yc : fit circle center (y-value) (float)
        R : fir circle radius (float)

    Output:
        None (generates matplotlib plot).
    """
    #f = plt.figure(facecolor='white')
    #plt.axis('equal')

    theta_fit = np.linspace(-pi, pi, 180)

    x_fit = xc + R*np.cos(theta_fit)
    y_fit = yc + R*np.sin(theta_fit)
    plt.plot(x_fit, y_fit, '--w' , label="fitted circle", lw=0.5)
    #plt.plot([xc], [yc], 'bD', mec='y', mew=1)
    #plt.xlabel('x')
    #plt.ylabel('y')
    # plot data
    #plt.scatter(x, y, c='red', label='data')

    #plt.legend(loc='best', labelspacing=0.1 )
    #plt.grid()
    #plt.title('Fit Circle')


def cutImage(fullimage, xmin, xmax, ymin, ymax, otname):
    newimg_data = []
    fullimage = fullimage
    print(fullimage)
    xmin = xmin
    xmax = xmax
    ymin = ymin
    ymax = ymax
    otname = otname
    #print(fullimage)
    #print(xmin)
    #print(xmax)
    #print(ymin)
    #print(ymax)

    # dir = "/history/"
    dir = "./"
    print(fullimage)
    cutimagepng = dir + fullimage[0:-4] + ".png"
    cutimagepng = dir + "obsimg.png"
    cutimagepng2 = dir + "obsimg2.png"
    print(f' cutimagepng is {cutimagepng}')

    with pyfits.open(fullimage) as hdul:
        print("@@@@@@@@@@@@@@@@@")
        #hdul.info()
        hdul.verify('fix')
        img_data = np.array(hdul[0].data)
        print("image shape", img_data.shape)
        #print(img_data)
        print(xmin)
        print(xmax)
        print(ymin)
        print(ymax)
        # print(len(img_data))
        # print(img_data.shape)
        newimg_data = img_data[ymin:ymax, xmin:xmax]
        # newimg_data = (newimg_data/np.max(newimg_data))*255
        # newimg_data = newimg_data.astype(np.uint8)
        newimg_data = zscale_image(newimg_data)
        rotateAngle = 210 #degree
        newimg_data = rotateImg(newimg_data, rotateAngle)
        #print(newimg_data)
        print("@@@@@@@@@@@@@@@@@")
        print(len(newimg_data))
        print(newimg_data.shape)
        
        pyfits.writeto(cutimagepng, newimg_data, header=None, overwrite=True)

        interval = ZScaleInterval()
        vmin, vmax = interval.get_limits(newimg_data)
        if vmax > vmin:
            vmax = vmin + ( vmax - vmin) * 1.5
        else:
            vmax =vmax + 100

        print(vmin)
        print(vmax)



        # plt.subplot(1, 1, 1)
        fig = plt.gcf()
        plt.axis('off')
        fig.set_size_inches(7.0 / 3, 7.0 / 3)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0, wspace=0)
        plt.margins(0, 0)
        print(f'will imshow')
        xm, ym = mark_ele_40deg("ele_data/a20")
        # xm, ym = mark_ele_40deg("/home/weamon/xsoft/newxgwacmatchsoft/ele_data/a20")
        #==============
        #all the values below are derived by the code:  circle_fit.py
       # #for ele=40 deg
       # xc = 2006.18123495101
       # yc = 1896.1487045835916
       # r = 1681.4121789004698
       # residual =  18.22752586012538
       # plot_data_circle(xm, ym, xc, yc, r)
       # #=============
       # #for ele=60 deg
       # xc = 2005.930582537869
       # yc = 1957.9809983248024
       # r = 815.8701292511745
       # residual = 0.726186332234487
       # plot_data_circle(xm, ym, xc, yc, r)
        # =============
        # for ele=20 deg
        xc = 1500
        yc = 1510
        r = 1200
        residual = 61.38078727770802
        plot_data_circle(xm, ym, xc, yc, r)
        #=============
       # # =============
       # # for ele=70 deg
       # xc = 2005.8262873969848
       # yc = 1969.7367211163116
       # r = 514.2351513164311
       # residual = 0.18168229839906444
       # plot_data_circle(xm, ym, xc, yc, r)
       # # =============
       # # =============
       # # for ele=50 deg
       # xc = 2006.0844142106594
       # yc = 1936.4956742987038
       # r = 1185.7030754961313
       # residual = 3.9412098829509183
       # plot_data_circle(xm, ym, xc, yc, r)
        # =============

        plt.imshow(newimg_data, cmap=plt.cm.gray, vmin=vmin, vmax=vmax,  origin='lower', aspect='equal')

        plt.savefig(fname=cutimagepng2, format='png', dpi=600,pad_inches = 0.0)
        #
        #plt.show()
        plt.close()   #之前的设置都不起作用了。
        img = Image.open(cutimagepng2)
        arr = np.asarray(img)
        # 打印数组维度
        print(arr.shape)
        #plt.imshow(arr)
        print(newimg_data.shape)
        #============
        # rotation -90deg  anticloud  
        #arr2 = arr.transpose(1, 0, 2)  # 行列转置
        #arr3 = arr2[::-1]
        # rotation -116deg
        #arr2 = arr.transpose(1, 0, 2)[::-1]  # 行列转置
        #arr3 = np.array(arr2[::-1])
        arr3 = arr
        #==============
        print(arr3.shape)
        xmax = arr3.shape[0]
        print(xmax)
        ymax = arr3.shape[1]
        print(ymax)
        plt.axis('off')
        fig.set_size_inches(7.0 / 3, 7.0 / 3)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0, wspace=0)
        plt.margins(0, 0)
        #modified by xlp at 20220128
        #points = circle_points(200, [ymax/2, xmax/2], ymax/2)[:-1]
        #plt.plot(points[:, 0], points[:, 1], '--w', lw=0.5)


        plt.imshow(arr3, cmap=plt.cm.gray, vmin=vmin, vmax=vmax - 20,  aspect='equal')

        print(f'have rotated')
        #plt.show()
        #plt.imshow(newimg_data, cmap=plt.cm.gray, vmin=vmin, vmax=vmax - 20, aspect='equal')
        #
      
        print(xmax)
        print(ymax)
        width = xmax - xmin
        high = ymax - ymin
        plt.text(xmax/2, 70, otname, fontsize=13, color="yellow", verticalalignment="bottom", horizontalalignment="center")
        #
        plt.text(xmax-200, 300, s='S', fontsize=10, color="white", verticalalignment="bottom",
                 horizontalalignment="center")
        plt.text(xmax-100, ymax-350, s='W', fontsize=10, color="white", verticalalignment="bottom",
                horizontalalignment="center")
        plt.text(220, 300, s='E', fontsize=10, color="white", verticalalignment="bottom",
                 horizontalalignment="center")
        plt.text(180, ymax-250, s='N', fontsize=10, color="white", verticalalignment="bottom",
                 horizontalalignment="center")
        #plt.text(xmax-200, 80, s='20d', fontsize=7, color="white", verticalalignment="bottom",
        #         horizontalalignment="center")
        plt.text(xmax-300, 200, s='20d', fontsize=7, color="white", verticalalignment="bottom",
                 horizontalalignment="center")

        #dir_data = sys.path[0]  #get the absolute path for current directory.
        #plt.savefig(dir="/disk2/test/xlp", fname=cutimage, format='png', dpi=300)
        #plt.savefig(dir=dir_data, fname=cutimage, format='png', dpi=300)
        #img.show(cutimagepng)
        #img.save(cutimagepng)
        #yc = ymax/2
        #xc = xmax/2
        #points = circle_points(200, [700, 700], 700)[:-1]
        #plt.plot(points[:, 0], points[:, 1], '-r', lw=1)
        #plt.ion()
        plt.savefig(fname=cutimagepng, format='png', dpi=600)
        #plt.show()
        #plt.pause(1)  # 显示秒数
        #plt.close()  # 关闭图片，并继续执行后续代码。





if __name__ == "__main__":
    img = "C20231110T114950.fit"
    xmin = 1
    xmax = 3008
    ymin = 1
    ymax = 3028-21
    otname = "test"
    # img = sys.argv[1]
    # xmin = int(sys.argv[2])
    # xmax = int(sys.argv[3])
    # ymin = int(sys.argv[4])
    # ymax = int(sys.argv[5])
    # otname = sys.argv[6]

    print(img)
    print(xmin)
    print(xmax)
    print(ymin)
    print(ymax)
    cutImage(fullimage=img, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, otname=otname)

