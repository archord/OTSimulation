
import math
from PIL import Image, ImageDraw, ImageOps, ImageFilter
import numpy as np
from scipy.ndimage.filters import gaussian_filter

def transPoint(p, arc, fromSize, toSize):
    
    CY = fromSize[0]/2 
    CX = fromSize[1]/2
    CY2 = toSize[0]/2 
    CX2 = toSize[1]/2 
    
    x0 = p[0] - CX
    y0 = -p[1] + CY
    sina = math.sin(arc)
    cosa = math.cos(arc)
    
    x = x0*cosa - y0*sina
    y = y0*cosa + x0*sina
    
    x = x + CX2
    y = CY2 - y
    
    return [int(x),int(y)]

def rotateImg3():

    imgPath="images/test2.png"
    # Open image, enforce RGB with alpha channel
    img = Image.open(imgPath).convert('RGBA')
    w, h = img.size

    # Set up edge margin to look for dominant color
    me = 3

    # Set up border margin to be added in dominant color
    mb = 30

    # On an image copy, set non edge pixels to (0, 0, 0, 0)
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    draw.rectangle((me, me, w - (me + 1), h - (me + 1)), (0, 0, 0, 0))

    # Count colors, first entry most likely is color used to overwrite pixels
    n_colors = sorted(img_copy.getcolors(2 * me * (w + h) + 1), reverse=True)
    dom_color = n_colors[0][1] if n_colors[0][1] != (0, 0, 0, 0) else n_colors[1][1]

    # Add border
    img = ImageOps.expand(img, mb, dom_color).convert('RGB')

    # Save image
    img.save('with_border.png')

def rotateImg1():
    

    imgPath="test2.png"
    img = Image.open(imgPath)
    im2 = img.convert('RGBA')
    rotateAngle=210  #degree
    rotImg = im2.rotate(rotateAngle, expand=0)
    fff = Image.new('RGBA', rotImg.size, (0,0,0,255))
    out = Image.composite(rotImg, fff, rotImg)
    rotImg.save("%s_rotate_%d.png"%(imgPath.split(".")[0], rotateAngle))
    
def rotateImg2():
    imgPath="images/test2.png"
    img = Image.open(imgPath)
    img = img.convert('RGBA')
    rotateAngle=210  #degree
    fillcolor = getBgColor(img)
    print("fillcolor",fillcolor)
    rotImg = img.rotate(rotateAngle, expand=0, fillcolor=fillcolor)
    rotImg.save("%s_rotate_%d.png"%(imgPath.split(".")[0], rotateAngle))

def getBgColor(img):

    w, h = img.size
    me = 3
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    draw.rectangle((me, me, w - (me + 1), h - (me + 1)), (0, 0, 0, 0))
    n_colors = sorted(img_copy.getcolors(2 * me * (w + h) + 1), reverse=True)
    dom_color = n_colors[0][1] if n_colors[0][1] != (0, 0, 0, 0) else n_colors[1][1]
    return dom_color

def extendImg(img):

    w, h = img.size
    maxSize = math.ceil(math.sqrt(w*w+h*h))
    print(w,h,maxSize)
    new_img = Image.new("RGBA", (maxSize, maxSize))
    # x0 = math.ceil((maxSize-w)/2)
    # y0 = math.ceil((maxSize-h)/2)
    # print(x0,y0)
    # new_img[y0:y0+h-1,x0:x0+w-1]=img
    old_size = (w,h)
    new_size = (maxSize, maxSize)
    box = tuple((n - o) // 2 for n, o in zip(new_size, old_size))
    new_img.paste(img, box)
    new_img.save("aaa.png")

def filterArray(img):

    timg = Image.fromarray(img)
    # timg.save("b1.png")
    timg2 = timg.filter(ImageFilter.GaussianBlur(radius= 5)) 
    # timg2 = timg.filter(ImageFilter.MedianFilter(size= 19)) 
    # timg2.save("b2.png")
    return np.array(timg2)

def extendImg2(img):

    oldImg = np.array(img)
    h, w, c = oldImg.shape
    maxSize = math.ceil(math.sqrt(w*w+h*h))
    newImg = np.zeros((maxSize, maxSize, c), dtype=np.uint8)
    print(w,h,maxSize)
    
    x0 = math.ceil((maxSize-w)/2)
    y0 = math.ceil((maxSize-h)/2)
    print(x0,y0)
    
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

    # Image.fromarray(newImg).save("aaa.png")
    return Image.fromarray(newImg), (x0,y0), (x0+w,y0+h)

def rotateImg4():
    imgPath="images/test2.png"
    img = Image.open(imgPath)
    img = img.convert('RGBA')
    w,h = img.size
    newImg, p0, p1 = extendImg2(img)

    rotateAngle=210  #degree
    fillcolor = (255,255,255,255)
    rotImg = newImg.rotate(rotateAngle, expand=1, fillcolor=fillcolor)
    newW, newH = rotImg.size

    rotImg = np.array(rotImg)
    print(w,h, newW, newH)
    print((newH-h)//2,(newW-w)//2)
    sub2=rotImg[(newH-h)//2:(newH-h)//2+h, (newW-w)//2:(newW-w)//2+w]
    # print(newImg.size, rotImg.shape, p0, p1)
    # p1 = transPoint([p0[0], p0[1]], rotateAngle/180, newImg.size, rotImg.shape)
    # p2 = transPoint([p1[0], p1[1]], rotateAngle/180, newImg.size, rotImg.shape)
    # print(p1, p2)
    # tbound = 20
    # tbound2 = 20
    
    # minx2 = (p1[0] if p1[0]<p2[0] else p2[0]) - tbound
    # maxx2 = (p1[0] if p1[0]>p2[0] else p2[0]) + tbound
    # miny2 = int((p1[1]+p2[1])/2 - tbound2)
    # maxy2 = int((p1[1]+p2[1])/2 + tbound2)
    
    # sub2 = rotImg[miny2:maxy2,minx2:maxx2]
    
    Image.fromarray(sub2, 'RGBA').save("%s_rotate_%d.png"%(imgPath.split(".")[0], rotateAngle))

if __name__ == "__main__":

    rotateImg4()