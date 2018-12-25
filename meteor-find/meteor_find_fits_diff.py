# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
from PIL import Image
import os
from astropy.io import fits
from astropy.stats import sigma_clip
#import gzip

def zscale_image(input_img, contrast=0.25):

    """This emulates ds9's zscale feature. Returns the suggested minimum and
    maximum values to display."""

    samples = input_img.flatten()
    samples = samples[~np.isnan(samples)]
    samples.sort()
    chop_size = int(0.10*len(samples))
    subset = samples[chop_size:-chop_size]

    i_midpoint = int(len(subset)/2)
    I_mid = subset[i_midpoint]

    fit = np.polyfit(np.arange(len(subset)) - i_midpoint, subset, 1)
    # fit = [ slope, intercept]

    z1 = I_mid + fit[0]/contrast * (1-i_midpoint)/1.0
    z2 = I_mid + fit[0]/contrast * (len(subset)-i_midpoint)/1.0

    return z1, z2
    
def lineDst(p1,p2):
    x=p1[0]-p2[0]
    y=p1[1]-p2[1]
    return math.sqrt(x*x+y*y)

def lineDistance(p0, p1, p2):
    
    x0 = p0[0]
    y0 = p0[1]
    x1 = p1[0]
    y1 = p1[1]
    x2 = p2[0]
    y2 = p2[1]
    
    ydiff = y1 - y2
    xdiff = x1 - x2
    B = math.sqrt(ydiff*ydiff + xdiff*xdiff)
    A = ydiff*x0 - xdiff*y0 + x2*y1 - y2*x1
    
    return A/B

#input is a binary image
def findCircle1(bimg):
    cimg, contours, hierarchy = cv2.findContours(bimg.copy(),cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    pi_4 = 4*math.pi
    circles = []
    for contour in contours:
        
        area = cv2.contourArea(contour)
        # there is one contour that contains all others, filter it out
        #if area > 500:
        #    continue
    
    
        arclen = cv2.arcLength(contour, True)
        circularity = (pi_4 * area) / (arclen * arclen)
        
        if circularity > 0.1: # XXX Yes, pretty low threshold.
            box = cv2.boundingRect(contour)
            tdia = (box[2] if box[2]>box[3] else box[3])
            radii = math.ceil(tdia/2)
            circles.append(((box[0] + int(box[2] / 2), box[1] + int(box[3] / 2)), radii, circularity))
                
        #m = cv2.moments(contour)
        #center = (int(m['m10'] / m['m00']), int(m['m01'] / m['m00']))
        #(centerX, centerY), radius
        #circles.append(((int(m['m10'] / m['m00']), int(m['m01'] / m['m00'])),radii))
    return circles
        
class MeteorRecognize:

    maxLineGap = 5
    maxLineLimit = 50
    #erodeKernel = np.ones((5,5),np.uint8)
    erodeKernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
    
    borderWidth = 50
    lineCluster = []
    validLines = []
    inValidLines = []
    
    
    def __init__(self):
        self.imgAvg1 = 0
        self.imgRms1 = 0
        self.thred1 = 0
        self.imgAvg2 = 0
        self.imgRms2 = 0
        self.thred2 = 0
        self.imgH = 0
        self.imgW = 0
        
        
    def showMeteor(self):
        
        tbound = 20
        tbound2 = 50
        tnum = len(self.validLines)
        figW = 3*2+2
        figH = tnum*3
        plt.figure(figsize=(figW,figH), dpi=80)
        
        i = 1
        img = Image.fromarray(self.img, 'L')
        for line in self.validLines:
            tline = line["maxLengthLine"]
            #max = (a if a > b else b) 
            minx = (tline[0] if tline[0]<tline[2] else tline[2]) - tbound
            maxx = (tline[0] if tline[0]>tline[2] else tline[2]) + tbound
            miny = (tline[1] if tline[1]<tline[3] else tline[3]) - tbound
            maxy = (tline[1] if tline[1]>tline[3] else tline[3]) + tbound
            
            rotImg, p1, p2 = self.rotateImg(img,line)
            minx2 = (p1[0] if p1[0]<p2[0] else p2[0]) - tbound
            maxx2 = (p1[0] if p1[0]>p2[0] else p2[0]) + tbound
            miny2 = int((p1[1]+p2[1])/2 - tbound2)
            maxy2 = int((p1[1]+p2[1])/2 + tbound2)
            
            sub1 = self.img[miny:maxy,minx:maxx]
            sub2 = rotImg[miny2:maxy2,minx2:maxx2]
            
            tidx = i*2-1
            ax = plt.subplot("%d2%d"%(tnum, tidx))
            ax.imshow(sub1, cmap='gray')
            plt.title("sub%d"%(i))
            plt.grid(color='w')
            
            tidx = i*2
            ax = plt.subplot("%d2%d"%(tnum, tidx))
            ax.imshow(sub2, cmap='gray')
            plt.title("rot%d"%(i))
            plt.grid(color='w')
                        
            i = i+ 1
        
        plt.show()
        #plt.savefig("E://aa.png")
        
    def transPoint(self, p, arc, fromSize, toSize):
     
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
        
    def rotateImg(self, img, line):
        
        tline = line["maxLengthLine"]
        tarc = math.atan2(tline[1]-tline[3], tline[0]-tline[2])
        #print("rotate angle: %f" %(tarc*180/math.pi))
        #img = Image.fromarray(self.img, 'L')
        rotImg = img.rotate(tarc*180/math.pi, expand=1)
        
        p1 = self.transPoint([tline[0], tline[1]], tarc, img.size, rotImg.size)
        p2 = self.transPoint([tline[2], tline[3]], tarc, img.size, rotImg.size)
        
        return np.array(rotImg), p1, p2
        
    def rotateLine(self, objLine, arcLine, fromSize, toSize):
        
        tarc = math.atan2(arcLine[1]-arcLine[3], arcLine[0]-arcLine[2])
        
        p1 = self.transPoint([objLine[0], objLine[1]], tarc, fromSize, toSize)
        p2 = self.transPoint([objLine[2], objLine[3]], tarc, fromSize, toSize)
        
        return p1, p2
           
    def findLine(self):
        
        img = fits.getdata(self.fullPath).astype(np.float32)
        img[img<0]=0
        img0 = fits.getdata(self.fullPath0).astype(np.float32)
        img0[img0<0]=0
        imgDiff = img.copy()-img0.copy()
        #imgDiff[imgDiff<0]=0
        #new_hdu = fits.PrimaryHDU(imgDiff)
        #new_hdu.writeto("f:/aa.fit")
        
        zimg = img.copy().astype(np.int)
        zmin, zmax = zscale_image(zimg)
        zimg[zimg>zmax] = zmax
        zimg[zimg<zmin] = zmin
        if zmin==zmax:
            self.lines = np.array([])
            return;
        
        zimg=(((zimg-zmin)/(zmax-zmin))*255).astype(np.uint8)
        
        '''
        Image.fromarray(zimg).save("f:/aa.png")
        zimg = imgDiff.copy().astype(np.int)
        zmin, zmax = zscale_image(zimg)
        zimg[zimg>zmax] = zmax
        zimg[zimg<zmin] = zmin
        zimg=(((zimg-zmin)/(zmax-zmin))*255).astype(np.uint8)
        Image.fromarray(zimg).save("f:/aa1.png")
        return
        '''
        
        zimgDiff = imgDiff.copy()
        zimgDiff[zimgDiff<0]=0
        tmin = zimgDiff.min()
        tmax = zimgDiff.max()
        
        if tmin==tmax:
            self.lines = np.array([])
            return;
        
        
        imgAvg = np.mean(zimgDiff)
        imgRms = np.std(zimgDiff)
        thred1 = imgAvg + 0.5 * imgRms
        self.imgAvg1 = imgAvg
        self.imgRms1 = imgRms
        self.thred1 = thred1
        print("avg1=%f;rms1=%f;tmax=%f;tmin=%f"%(imgAvg,imgRms,tmax, tmin))
        
        zimgDiff = cv2.medianBlur(zimgDiff,3) #medianBlur  blur
        
        tmin = zimgDiff.min()
        tmax = zimgDiff.max()
        imgAvg = np.mean(zimgDiff)
        imgRms = np.std(zimgDiff)
        thred1 = imgAvg + 0.5 * imgRms
        self.imgAvg1 = imgAvg
        self.imgRms1 = imgRms
        self.thred1 = thred1
        print("avg1=%f;rms1=%f;tmax=%f;tmin=%f"%(imgAvg,imgRms,tmax, tmin))
        
        zimgDiff=(((zimgDiff-tmin)/(tmax-tmin))*255.0).astype(np.uint8)
        Image.fromarray(zimgDiff).save("f:/a1.png")
        
        self.img = img
        self.zimg = zimg
        self.imgDiff = imgDiff
        self.zimgDiff = zimgDiff
                
        self.imgH = img.shape[0]
        self.imgW = img.shape[1]
        
        #drop image border 20pix
        #zimgDiff[0:self.borderWidth, :] = 0
        #zimgDiff[:, 0:self.borderWidth] = 0
        #zimgDiff[self.imgH-self.borderWidth:self.imgH, :] = 0
        #zimgDiff[:, self.imgW-self.borderWidth:self.imgW] = 0
        
        imgAvg = np.mean(zimgDiff)
        imgRms = np.std(zimgDiff)
        thred1 = imgAvg + 3 * imgRms
        self.imgAvg1 = imgAvg
        self.imgRms1 = imgRms
        self.thred1 = thred1
        print("avg1=%f;rms1=%f;thred1=%f"%(imgAvg,imgRms,thred1))
        
        #new_hdu = fits.PrimaryHDU(zimgDiff)
        #new_hdu.writeto("f:/ab.fit")
        
        zimgDiff[zimgDiff<thred1]=0
        #Image.fromarray(zimgDiff).save("f:/a2.png")
        #return
        
        timg1 = zimgDiff[zimgDiff>thred1]
        if len(timg1) == 0:
            self.lines = np.array([])
            print(123)
            return
                        
        filtered_data = sigma_clip(timg1, sigma=3, iters=2, copy=False)
        imgbg = filtered_data.data[~filtered_data.mask]
        
        imgAvg = np.average(imgbg)
        imgRms = np.std(imgbg)        
        #thred2 = imgAvg + 3 * imgRms
        thred2 = imgAvg + 2 * imgRms
        self.imgAvg2 = imgAvg
        self.imgRms2 = imgRms
        self.thred2 = thred2
        print("avg1=%f;rms1=%f;thred2=%f"%(imgAvg,imgRms,thred2))
        
        thred2 = (145 if thred2>145 else thred2)
        
        #flag,bimg = cv2.threshold(img,0,255,cv2.THRESH_OTSU)
        flag,bimg = cv2.threshold(zimgDiff,thred2,255,cv2.THRESH_BINARY)
        Image.fromarray(bimg).save("f:/aa1.png")
        
        rho = 1
        theta = np.pi/180
        #lines = cv2.HoughLinesP(bimg, rho = rho, theta = theta, threshold = 10,
        #                        minLineLength = 50,maxLineGap = self.maxLineGap)
        #寻找暗的轨迹
        #lines = cv2.HoughLinesP(bimg, rho = rho, theta = theta, threshold = 20,
        #        minLineLength = 50,maxLineGap = 20)
        #寻找亮的轨迹，亮的流星
        lines = cv2.HoughLinesP(bimg, rho = rho, theta = theta, threshold = 50,
                minLineLength = 50,maxLineGap = self.maxLineGap)
                
        while lines is None and thred2>100:
            #flag,bimg = cv2.threshold(img,0,255,cv2.THRESH_OTSU)
            flag,bimg = cv2.threshold(zimgDiff,thred2,255,cv2.THRESH_BINARY)
            lines = cv2.HoughLinesP(bimg, rho = rho, theta = theta, threshold = 50,
                    minLineLength = 50,maxLineGap = self.maxLineGap)
            
            if lines is None:
                thred2 = thred2 - 5
                
        lines = (np.array([]) if lines is None else lines)
        print("thred1: %f thred2: %f lines: %d"%(thred1, thred2, lines.shape[0]))
        
        self.bimg = bimg
        self.lines = lines
        #print("number of lines: %d" % (lines.shape[0]))
                
    #maxSlope=10, maxOrigDist=300, maxCenterDist=50
    def clusterByDst(self, maxSlope=5, maxOrigDist=150, maxCenterDist=50, maxClusterCenterDist=500):
        
        arc2ang = 180/math.pi
        p0 = (self.imgW/2, self.imgH/2)
        
        tcluster = []
        for tidx, tline in enumerate(self.lines):
            tline = tline[0]
            p1 = (tline[0],tline[1])
            p2 = (tline[2],tline[3])
            cx = int((tline[0]+tline[2])/2)
            cy = int((tline[1]+tline[3])/2)
            tcenter =  [cx, cy] 
            
            slope = math.atan2(p1[1]-p2[1],p1[0]-p2[0])*arc2ang
            origDist = lineDistance(p0, p1, p2)
            
            if not tcluster:
                tcluster.append({"avgSlope":slope, "avgOrigDist":origDist, 
                                 "slope":[slope],"origDist":[origDist], "line":[tline],
                                "avgCenter":tcenter,"lineCenter":[tcenter]})
            else:
                isMatch = False
                for tc in tcluster:
                    flag3 = lineDst(tcenter,tc["avgCenter"])<maxCenterDist
                    if flag3:
                        tc["line"].append(tline)
                        tc["slope"].append(slope)
                        tc["origDist"].append(origDist)
                        tc["lineCenter"].append(tcenter)
                        tc["avgSlope"] = np.mean(np.array(tc["slope"]))
                        tc["avgOrigDist"] = np.mean(np.array(tc["origDist"]))
                        tc["avgCenter"] = np.mean(np.array(tc["lineCenter"]), axis=0)
                        
                        isMatch = True
                        break
                if not isMatch:
                    tcluster.append({"avgSlope":slope, "avgOrigDist":origDist, 
                                 "slope":[slope],"origDist":[origDist], "line":[tline],
                                "avgCenter":tcenter,"lineCenter":[tcenter]})
        tlines2 = []
        tcluster2 = []
        #print(len(tcluster))
        for tc in tcluster:
            if len(tc["line"])==1:
                tlines2.append(tc["line"])
            else:
                tcluster2.append(tc)
        
        #**************************************** todo
        tcluster3 = []
        while len(tcluster2)>0:
            notMatch = []
            tline2 = tcluster2.pop()
            while len(tcluster2)>0:
                tc = tcluster2.pop()
                flag1 = abs(tc["avgSlope"]-tline2["avgSlope"])<maxSlope
                flag2 = abs(tc["avgOrigDist"]-tline2["avgOrigDist"])<maxOrigDist
                flag3 = lineDst(tc["avgCenter"],tline2["avgCenter"])<maxClusterCenterDist
                if (flag1 and flag2 and flag3):
                    tline2["line"].extend(tc["line"])
                    tline2["slope"].extend(tc["slope"])
                    tline2["origDist"].extend(tc["origDist"])
                    tline2["lineCenter"].extend(tc["lineCenter"])
                    tline2["avgSlope"] = np.mean(np.array(tline2["slope"]))
                    tline2["avgOrigDist"] = np.mean(np.array(tline2["origDist"]))
                    tline2["avgCenter"] = np.mean(np.array(tline2["lineCenter"]), axis=0)
                else:
                    notMatch.append(tc)
            tcluster2 = notMatch
            tcluster3.append(tline2)
                        
        '''             
        for tc in tcluster2:
            tSlope = np.array(tc["slope"])
            tAvgS = np.mean(tSlope)
            tidx = np.argmin(np.abs(tSlope-tAvgS))
            tlines2.append([tc["line"][tidx]])
        '''          
        #tcluster = []
        tcluster = tcluster3
        for tline in tlines2:
            tline = tline[0]
            p1 = (tline[0],tline[1])
            p2 = (tline[2],tline[3])
            cx = int((tline[0]+tline[2])/2)
            cy = int((tline[1]+tline[3])/2)
            tcenter =  [cx, cy] 
            
            slope = math.atan2(p1[1]-p2[1],p1[0]-p2[0])*arc2ang
            origDist = lineDistance(p0, p1, p2)
            
            if not tcluster:
                tcluster.append({"avgSlope":slope, "avgOrigDist":origDist, 
                                 "slope":[slope],"origDist":[origDist], "line":[tline],
                                "avgCenter":tcenter,"lineCenter":[tcenter]})
            else:
                isMatch = False
                for tc in tcluster:
                    flag1 = abs(tc["avgSlope"]-slope)<maxSlope
                    flag2 = abs(tc["avgOrigDist"]-origDist)<maxOrigDist
                    flag3 = lineDst(tcenter,tc["avgCenter"])<maxClusterCenterDist
                    if (flag1 and flag2 and flag3):
                        tc["line"].append(tline)
                        tc["slope"].append(slope)
                        tc["origDist"].append(origDist)
                        tc["avgSlope"] = np.mean(np.array(tc["slope"]))
                        tc["avgOrigDist"] = np.mean(np.array(tc["origDist"]))
                        tc["lineCenter"].append(tcenter)
                        tc["avgCenter"] = np.mean(np.array(tc["lineCenter"]), axis=0)
                        isMatch = True
                        break
                if not isMatch:
                    tcluster.append({"avgSlope":slope, "avgOrigDist":origDist, 
                                 "slope":[slope],"origDist":[origDist], "line":[tline],
                                "avgCenter":tcenter,"lineCenter":[tcenter]})
                
        #print("cluster number: %d" % (len(tcluster)))
        self.lineCluster = tcluster
        
 
    def filteCluster(self):
        
        self.inValidLines = []
        self.validLines = []
        
        arc2ang = 180/math.pi
        
        for tc in self.lineCluster:
            slopes = []
            for line in tc["line"]:
                for x1,y1,x2,y2 in [line]:
                    slopes.append(math.atan2(y1-y2,x1-x2)*arc2ang)
            #print(slopes)
            if len(slopes)>1:
                slopeRms = np.std(slopes)
            else:
                slopeRms = 0
                
            tc["slopeRms"] = slopeRms
            if slopeRms>2:
                tc["valid"] = False
                self.inValidLines.append(tc)
            else:
                tc["valid"] = True
                self.validLines.append(tc)
            
        
    def mergeCluster(self):
        
        #for tc in self.validLines:
        for tc in self.lineCluster:
            xmin = self.imgW
            xmax = 0
            ymin = self.imgH
            ymax = 0
            #print(tc["avgCenter"])
            for line in tc["line"]:
                for x1,y1,x2,y2 in [line]:
                    if x1 < xmin:
                        xmin = x1
                    if x2 < xmin:
                        xmin = x2
                    if x1 > xmax:
                        xmax = x1
                    if x2 > xmax:
                        xmax = x2
                        
                    if y1 < ymin:
                        ymin = y1
                    if y2 < ymin:
                        ymin = y2
                    if y1 > ymax:
                        ymax = y1
                    if y2 > ymax:
                        ymax = y2
            tline = tc["line"][0]
            if tline[1]<tline[3]:
                tc["maxLengthLine"] = [xmin, ymin, xmax, ymax]
            else:
                tc["maxLengthLine"] = [xmin, ymax, xmax, ymin]
            
            tl2 = tc["maxLengthLine"]
            tc["maxLength"] = lineDst((tl2[0], tl2[1]),(tl2[2], tl2[3]))
            
            #print(tc["line"])
            #print(tc["maxLengthLine"])
    
      
    def cutRotateMeteorPng(self, savePath):
        
        if len(self.lineCluster)==0:
            return
        
        tbound = 50
        tbound2 = 50
        
        i = 1
        img = Image.fromarray(self.img, 'L')
        for line in self.validLines:
            
            rotImg, p1, p2 = self.rotateImg(img,line)
            minx2 = (p1[0] if p1[0]<p2[0] else p2[0]) - tbound
            maxx2 = (p1[0] if p1[0]>p2[0] else p2[0]) + tbound
            miny2 = int((p1[1]+p2[1])/2 - tbound2)
            maxy2 = int((p1[1]+p2[1])/2 + tbound2)
            
            sub2 = rotImg[miny2:maxy2,minx2:maxx2]
            
            tPath = "%s/%s_meteor%02d_%d_%f.png" % \
                (savePath, os.path.splitext(self.imgName)[0], i, lineDst(p1,p2), line["slopeRms"])
            Image.fromarray(sub2, 'L').save(tPath)
                  
            i = i+ 1
      
    def cutRotateMeteorPng_Debug(self, savePath):
        
        if len(self.lineCluster)==0:
            return
        
        tbound = 50
        tbound2 = 50
        
        i = 1
        img = Image.fromarray(self.img, 'L')
        for line in self.validLines:
            
            rotImg, p1, p2 = self.rotateImg(img,line)
            
            tPath = "%s/%s_meteor%02d_%d_%f.png" % \
                (savePath, os.path.splitext(self.imgName)[0], i, lineDst(p1,p2), line["slopeRms"])
            tPath3 = "%s/%s_meteor%02d_bin.png" % (savePath, os.path.splitext(self.imgName)[0], i)
            
            minx2 = (p1[0] if p1[0]<p2[0] else p2[0]) - tbound
            maxx2 = (p1[0] if p1[0]>p2[0] else p2[0]) + tbound
            miny2 = int((p1[1]+p2[1])/2 - tbound2)
            maxy2 = int((p1[1]+p2[1])/2 + tbound2)
            
            sub2 = rotImg[miny2:maxy2,minx2:maxx2]
            
            flag,bimg = cv2.threshold(sub2,0,255,cv2.THRESH_OTSU)
            #Image.fromarray(bimg, 'L').save(tPath3)
            
            bimg=cv2.erode(bimg, self.erodeKernel)
            bimg=cv2.dilate(bimg, self.erodeKernel)
            Image.fromarray(bimg, 'L').save(tPath3)
            '''
            circles = findCircle1(bimg)
            
              
            #sub1Img = Image.fromarray(sub2, 'L')
            sub1Img = Image.fromarray(sub2)
            sub1Img = sub1Img.convert('RGB')
            sub2 = np.array(sub1Img)
            
            cv2.line(sub2,(p1[0]-minx2,p1[1]-miny2),(p2[0]-minx2,p2[1]-miny2),(255,0,0),1)
            
            print("There are {} circles".format(len(circles)))
                 
            for tidx, tcircle in enumerate(circles):
                if tcircle[2]>0.8:
                    cv2.circle(sub2, tcircle[0], 3, (0, 255, 0), -1)
                    cv2.circle(sub2, tcircle[0], tcircle[1], (0, 255, 0), 1)
                else:
                    cv2.circle(sub2, tcircle[0], 3, (0, 0, 255), -1)
                    cv2.circle(sub2, tcircle[0], tcircle[1], (0, 255, 255), 1)
            '''    
            Image.fromarray(sub2).save(tPath)
                  
            i = i+ 1
         
    def cutRotateMeteor(self):
        
        if len(self.lineCluster)==0:
            return
        
        tbound = 0
        tbound2 = 50
        
        i = 1
        img = Image.fromarray(self.img, 'L')
        bimg = Image.fromarray(self.bimg, 'L')
        for line in self.lineCluster:
            
            if line["valid"] == True:
            
                rotImg, p1, p2 = self.rotateImg(img,line)
                rotbImg, p1, p2 = self.rotateImg(bimg,line)
                
                minx2 = (p1[0] if p1[0]<p2[0] else p2[0]) - tbound
                maxx2 = (p1[0] if p1[0]>p2[0] else p2[0]) + tbound
                miny2 = int((p1[1]+p2[1])/2 - tbound2)
                maxy2 = int((p1[1]+p2[1])/2 + tbound2)
                
                sub2 = rotImg[miny2:maxy2,minx2:maxx2]
                sub2b = rotbImg[miny2:maxy2,minx2:maxx2]
                sub2 = sub2.reshape(sub2.shape[0], sub2.shape[1],1).repeat(3,2)
                sub2b = sub2b.reshape(sub2b.shape[0], sub2b.shape[1],1).repeat(3,2)
                sub2line = sub2.copy()
                
                for tline in line["line"]:
                    tp1, tp2 = self.rotateLine(tline, line["maxLengthLine"], img.size, rotImg.shape)
                    cv2.line(sub2line,(tp1[0]-minx2,tp1[1]-miny2),(tp2[0]-minx2,tp2[1]-miny2),(0,255,0),1)
                cv2.line(sub2line,(p1[0]-minx2,p1[1]-miny2),(p2[0]-minx2,p2[1]-miny2),(255,0,0),1)
                
                sub2Con = np.concatenate((sub2, sub2b, sub2line), axis=0)
                line["rotateImgCon"] = sub2Con
                  
            i = i+ 1
         
    def saveCutRotateMeteor(self, savePath):
        
        if len(self.lineCluster)==0:
            return
        
        i = 1
        for line in self.validLines:
            
            if line["valid"] == True:
                
                tPath = "%s/%s_meteor%02d_%d_%f.png" % \
                    (savePath, os.path.splitext(self.imgName)[0], i, line["maxLength"], line["slopeRms"])
      
                Image.fromarray(line["rotateImgCon"]).save(tPath)
            i = i+ 1
    
    
    def saveSubFits(self, dpath, spath, line, i):
        
        tPath = "%s/%s_%03d.fits" % (dpath, os.path.splitext(self.imgName)[0], i)
        if os.path.exists(tPath):
            tPath = "%s/%s_%03d_rep.fits" % (dpath, os.path.splitext(self.imgName)[0], i)
    
        tp = line["maxLengthLine"]
        endpoint="[%d,%d,%d,%d]" % (tp[0],tp[1],tp[2],tp[3])
        
        new_hdu = fits.PrimaryHDU(line["FitsImgCon"])
        phdr = new_hdu.header
        phdr.set('path',spath)
        phdr.set('name',self.imgName)
        phdr.set('endpoint',endpoint)
        phdr.set('avgSlope',line["avgSlope"])
        phdr.set('avg1',self.imgAvg1)
        phdr.set('rms1',self.imgRms1)
        phdr.set('thred1',self.thred1)
        phdr.set('avg2',self.imgAvg2)
        phdr.set('rms2',self.imgRms2)
        phdr.set('thred2',self.thred2)
        #print(phdr)
        
        new_hdu.writeto(tPath)
    
    def cutRotateMeteorPlotPng(self, savePath, spath):
        
        if len(self.lineCluster)==0:
            return
        
        self.cutRotateMeteor()
        i = 1
        for line in self.validLines:
            
            if line["valid"] == True:
                
                tPath = "%s/%s_%03d.png" % (savePath, os.path.splitext(self.imgName)[0], i)
      
                #Image.fromarray(line["rotateImgCon"]).save(tPath)
                Image.fromarray(line["origImgCon"]).save(tPath)
                self.saveSubFits(savePath, spath, line, i)
                
            i = i+ 1
             
            
    def cutOrigMeteor(self):
        
        if self.lines is None:
            return
        
        if len(self.lineCluster)==0:
            return
        
        tbound = 50
        
        i = 1
        for line in self.lineCluster:
        #for line in self.validLines:
        #for line in self.inValidLines: 
            
            tline = line["maxLengthLine"]
            minx = (tline[0] if tline[0]<tline[2] else tline[2]) - tbound
            maxx = (tline[0] if tline[0]>tline[2] else tline[2]) + tbound
            miny = (tline[1] if tline[1]<tline[3] else tline[3]) - tbound
            maxy = (tline[1] if tline[1]>tline[3] else tline[3]) + tbound
            
            minx = (0 if minx<0 else minx)
            maxx = (self.imgW if maxx>self.imgW else maxx)
            miny = (0 if miny<0 else miny)
            maxy = (self.imgH if maxy>self.imgH else maxy)
            
            sub1 = self.img[miny:maxy,minx:maxx].astype(np.int32)
            sub1d = self.imgDiff[miny:maxy,minx:maxx].astype(np.int32)
            sub1z = self.zimg[miny:maxy,minx:maxx].astype(np.uint8)
            sub1b = self.bimg[miny:maxy,minx:maxx].astype(np.uint8)
            sub1dz = self.zimgDiff[miny:maxy,minx:maxx].astype(np.uint8)
            
            zmin, zmax = zscale_image(sub1dz)
            if zmax!=zmin:
                sub1dz[sub1dz>zmax] = zmax
                sub1dz[sub1dz<zmin] = zmin
                sub1dz=(((sub1dz-zmin)/(zmax-zmin))*255).astype(np.uint8)
            
                        
            #repeat(3,2)转换为彩色，代表将axis=2的维度每个元素重复3次 
            sub1z = sub1z.reshape(sub1z.shape[0], sub1z.shape[1],1).repeat(3,2)
            sub1dz = sub1dz.reshape(sub1dz.shape[0], sub1dz.shape[1],1).repeat(3,2)
            sub1b = sub1b.reshape(sub1b.shape[0], sub1b.shape[1],1).repeat(3,2)
            sub1line = sub1z.copy()
            
            for tl in line["line"]:   
                for x1,y1,x2,y2 in [tl]:       
                    cv2.line(sub1line,(x1-minx,y1-miny),(x2-minx,y2-miny),(0,255,0),1)
            
            cv2.line(sub1line,(tline[0]-minx,tline[1]-miny),(tline[2]-minx,tline[3]-miny),(255,0,0),1)
            
            sub2Con = np.concatenate((sub1z, sub1dz, sub1b, sub1line), axis=0)
            sub2ConFits = np.concatenate((sub1, sub1d), axis=0)
            line["origImgCon"] = sub2Con
            line["FitsImgCon"] = sub2ConFits
            
            i = i+ 1     
            
            
    def cutOrigMeteorPng_Debug(self, savePath):
        
        if len(self.lineCluster)==0:
            return
        
        tbound = 50
        
        i = 1
        for line in self.lineCluster:
        #for line in self.validLines:
        #for line in self.inValidLines: 
        
            print("avgSlope:%f, avgOrigDist:%f, slopeRms:%f" % \
                (line["avgSlope"], line["avgOrigDist"], line["slopeRms"]))
            
            tline = line["maxLengthLine"]
            minx = (tline[0] if tline[0]<tline[2] else tline[2]) - tbound
            maxx = (tline[0] if tline[0]>tline[2] else tline[2]) + tbound
            miny = (tline[1] if tline[1]<tline[3] else tline[3]) - tbound
            maxy = (tline[1] if tline[1]>tline[3] else tline[3]) + tbound
            
            minx = (0 if minx<0 else minx)
            maxx = (self.imgW if maxx>self.imgW else maxx)
            miny = (0 if miny<0 else miny)
            maxy = (self.imgH if maxy>self.imgH else maxy)
            
            sub1 = self.img[miny:maxy,minx:maxx]
            
            tPath = "%s/%s_meteor%02d_%d_%f.png" % \
                (savePath, os.path.splitext(self.imgName)[0], i, \
                 lineDst([tline[0],tline[1]],[tline[2],tline[3]]), line["slopeRms"])
            Image.fromarray(sub1).save(tPath)
            
            '''  '''
            #sub1Img = Image.fromarray(sub1, 'L')
            sub1Img = Image.fromarray(sub1)
            sub1Img = sub1Img.convert('RGB')
            sub1Img = np.array(sub1Img)
            
            cv2.line(sub1Img,(tline[0]-minx,tline[1]-miny),(tline[2]-minx,tline[3]-miny),(0,255,0),1)
            '''   '''   
            for tline in line["line"]:   
                for x1,y1,x2,y2 in [tline]:       
                    cv2.line(sub1Img,(x1-minx,y1-miny),(x2-minx,y2-miny),(255,0,0),1)
                    
            tPath2 = "%s/%s_meteor%02d_bin.png" % (savePath, os.path.splitext(self.imgName)[0], i)
            Image.fromarray(sub1Img).save(tPath2)
            
            i = i+ 1
        
    def recognizeLine(self, path, name, name0):   
        
        self.imgPath = path
        self.imgName = name
        self.imgName0 = name0
        self.fullPath = "%s/%s"%(path,name)
        self.fullPath0 = "%s/%s"%(path,name0)
        
        self.findLine()
        
    def clusterFilterLine(self):
        if self.lines is None:
            print("cannot find line")
        elif len(self.lines)>self.maxLineLimit:
            print("%d lines beyond %d, drop this image" %(len(self.lines), self.maxLineLimit))
        else:
            self.clusterByDst()
            self.filteCluster()
            self.mergeCluster()
            print("\ttotal %d lines, cluster to %d lines, with %d valid lines" % 
                (self.lines.shape[0], len(self.lineCluster), len(self.validLines)))

def saveSubFits(dpath, mrObj, spath, line):

    tp = line["maxLengthLine"]
    endpoint="[%d,%d,%d,%d]" % (tp[0],tp[1],tp[2],tp[3])
    
    new_hdu = fits.PrimaryHDU(line["FitsImgCon"])
    phdr = new_hdu.header
    phdr.set('path',spath)
    phdr.set('name',mrObj.imgName)
    phdr.set('endpoint',endpoint)
    phdr.set('avgSlope',line["avgSlope"])
    phdr.set('avg1',mrObj.imgAvg1)
    phdr.set('rms1',mrObj.imgRms1)
    phdr.set('thred1',mrObj.thred1)
    phdr.set('avg2',mrObj.imgAvg2)
    phdr.set('rms2',mrObj.imgRms2)
    phdr.set('thred2',mrObj.thred2)
    #print(phdr)
    
    new_hdu.writeto(dpath)
    
if __name__ == '__main__':
    
    spath = r'E:\work\program\python\OTSimulation\meteor-find'
    dpath = r'E:\work\program\python\OTSimulation\meteor-find'

    imgName = r"G044_mon_objt_180416T12270444.fit"
    imgName0 = r"G044_mon_objt_180416T12271944.fit"
    
    mr = MeteorRecognize()
    mr.recognizeLine(spath, imgName, imgName0)
    mr.clusterFilterLine()
    #mr.cutOrigMeteor()
    #mr.showMeteor()
    #mr.cutRotateMeteorPlotPng(dpath)
    #mr.cutOrigMeteor()
    '''
    for idx, line1 in enumerate(mr.validLines):
        img1 = line1["origImgCon"]
        tpath1 = "%s/%d.png"%(dpath, idx)
        tpath2 = "%s/%d.fits"%(dpath, idx)
        Image.fromarray(img1).save(tpath1)
        saveSubFits(tpath2, mr, imgName, line1)
    '''
