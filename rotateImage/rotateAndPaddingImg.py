
import math
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import numpy as np

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
    tpadd = oldImg[0:5,:]
    tpadd = np.mean(tpadd, axis=0)
    # print(tpadd.shape)
    # newImg[0:y0,x0:x0+w]=oldImg[0,:]
    newImg[0:y0,x0:x0+w]=tpadd
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

def rotateImg():
    imgPath="images/test2.png"
    img = Image.open(imgPath)
    img = img.convert('RGBA')
    w,h = img.size
    newImg = extendImg(img)

    rotateAngle=210  #degree
    fillcolor = (255,255,255,255)
    rotImg = newImg.rotate(rotateAngle, expand=1, fillcolor=fillcolor)
    newW, newH = rotImg.size
    # rotImg = np.array(rotImg)
    # sub2=rotImg[(newH-h)//2:(newH-h)//2+h, (newW-w)//2:(newW-w)//2+w]
    # Image.fromarray(sub2, 'RGBA').save("%s_rotate_%d.png"%(imgPath.split(".")[0], rotateAngle))
    cropImg = rotImg.crop(((newW-w)//2,(newH-h)//2, (newW-w)//2+w,(newH-h)//2+h))
    cropImg.save("%s_rotate_%d.png"%(imgPath.split(".")[0], rotateAngle))

if __name__ == "__main__":

    rotateImg()