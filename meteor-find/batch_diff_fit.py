# -*- coding: utf-8 -*-
import os
import numpy as np
from PIL import Image
from meteor_find_fits_diff import MeteorRecognize
import shutil
from astropy.io import fits


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
    
#limit: require the file at least have two lines
def getLastLine(fname):
    f = open(fname, 'rb')
    last = ""
    try:
        f.seek(-2, os.SEEK_END)     # Jump to the second last byte.
        while f.read(1) != b"\n":   # Until EOL is found...
            f.seek(-2, os.SEEK_CUR) # ...jump back the read byte plus one more.
        last = f.readline().decode()         # Read last line.
        #last = f.readlines()[-1].decode()
    finally:
        f.close()
    return last
    
def findMeteors2(spath, dpath, dpathMatch, objTotalMatchNumber):

    print('start find meteor from %s' % (spath))
    
    if not os.path.exists(dpath):
        os.makedirs(dpath)
    if not os.path.exists(dpathMatch):
        os.makedirs(dpathMatch)
            
    tempFitsName = r"G022_mon_objt_181214T09591991.fit.fz"

    sdirall = os.listdir(spath)
    sdirall.sort()
    sdir = []
    for t in sdirall:
        if t[-2:]=="fz" and len(t)==len(tempFitsName):
            sdir.append(t)
    
    mrlist = []
    continueFileName = ""
    continueFlag = False
    
    logfName0 = "%s_progress.txt" %(dpath)
    if os.path.exists(logfName0) and os.stat(logfName0).st_size > 0:
        continueFileName = getLastLine(logfName0)
        if len(continueFileName)>2:
            continueFileName=continueFileName.strip()
        
    logfile0 = open(logfName0, 'a')
    logfile0.write("\n\n")
    
    logfName1 = "%s_bad_log1.txt" %(dpath)
    logfName2 = "%s_good_log2.txt" %(dpath)
    logfile1 = open(logfName1, 'w')
    logfile2 = open(logfName2, 'w')
    
    for idx, fname in enumerate(sdir):
        
        tfname = fname
        if (not continueFlag) and (len(continueFileName)==len(tempFitsName)):
            if tfname!=continueFileName:
                continue
            else:
                continueFlag = True
                continue
        
        logfile0.write("%s\n"%(tfname))
        
        if fname[15:21]=="000000":
            continue
        
        if idx>0:
            print("%04d start process %s ..." % (idx, tfname))     
            timage0 = sdir[idx-1]
            mr = MeteorRecognize()
            mr.recognizeLine(spath, tfname, timage0)
            
            if mr.lines is None:
                continue
            
            #监测单帧异常帧，如转台的突然抖动，或出现大量假移动目标
            if mr.imgAvg1 > 4:
                logfile1.write("%d %s %.2f %.2f %.2f %.2f %.2f %.2f\n" % (idx, mr.imgName, mr.imgAvg1, \
                      mr.imgRms1,mr.thred1,mr.imgAvg2, mr.imgRms2,mr.thred2))
                if idx>1:
                    timage0 = sdir[idx-2]
                    mr.recognizeLine(spath, tfname, timage0)
                    if mr.lines is None:
                        continue
                    if mr.imgAvg1 > 5:
                        logfile1.write("%d %s %.2f %.2f %.2f %.2f %.2f %.2f\n" % (idx, mr.imgName, mr.imgAvg1, \
                           mr.imgRms1,mr.thred1,mr.imgAvg2, mr.imgRms2,mr.thred2))
                        continue
                else:
                    continue
                
            logfile2.write("%d %s %.2f %.2f %.2f %.2f %.2f %.2f\n" % (idx, mr.imgName, mr.imgAvg1, \
                mr.imgRms1,mr.thred1,mr.imgAvg2, mr.imgRms2,mr.thred2))
                            
            mr.clusterFilterLine()
            #mr.cutRotateMeteor()
            mr.cutOrigMeteor()
            
            #初始化匹配目标全局编号
            for tline in mr.validLines:
                tline["matchNumber"] = 0
                
            mrlist.append(mr)
            
            if len(mrlist)>1:
                mr1 = mrlist[0]
                mr2 = mrlist[1]
                i = 1
                for line1 in mr1.validLines:
                    slop1 = line1["avgSlope"]
                    for line2 in mr2.validLines:
                        slop2 = line2["avgSlope"]
                        slopdiff = abs(slop1-slop2)
                        if slopdiff<5:
                            line1["valid"]=False
                            line2["valid"]=False
                            if line1["matchNumber"]==0:
                                objTotalMatchNumber = objTotalMatchNumber + 1
                                line1["matchNumber"]=objTotalMatchNumber
                            if line2["matchNumber"]==0:
                                line2["matchNumber"]=line1["matchNumber"]
                            ''' '''
                            img1 = line1["origImgCon"]
                            img2 = line2["origImgCon"]
                            
                            
                            tPath1 = "%s/%06d_%s.png" % (dpathMatch, line1["matchNumber"], mr1.imgName.split('.')[0])
                            tPath2 = "%s/%06d_%s.png" % (dpathMatch, line2["matchNumber"], mr2.imgName.split('.')[0])
                            tPath3 = "%s/%06d_%s.fits" % (dpathMatch, line1["matchNumber"], mr1.imgName.split('.')[0])
                            tPath4 = "%s/%06d_%s.fits" % (dpathMatch, line2["matchNumber"], mr2.imgName.split('.')[0])
                  
                            if not os.path.exists(tPath1):
                                Image.fromarray(img1).save(tPath1)
                            if not os.path.exists(tPath2):
                                Image.fromarray(img2).save(tPath2)
                            if not os.path.exists(tPath3):
                                saveSubFits(tPath3, mr1, spath, line1)
                            if not os.path.exists(tPath4):
                                saveSubFits(tPath4, mr2, spath, line2)
                            
                            #break
                    i = i + 1
                #mr1.saveCutRotateMeteor(dpath)
                mr1.cutRotateMeteorPlotPng(dpath, spath)
                mrlist.pop(0)
            
                #if idx > 5:
                #    break
            
    logfile0.close()
    logfile1.close()
    logfile2.close()
    print('total process %d image.' % (len(sdir)))
    
def processAllCCD():
    
    objTotalMatchNumber = 0
    
    spath = r'/home/xy/Downloads/myresource/deep_data2/G180216/17320495.0'
    dpath = r'/home/xy/Downloads/myresource/deep_data2/simot/meteor_181224/meteor_result'
    dpathMatch = r'/home/xy/Downloads/myresource/deep_data2/simot/meteor_181224/meteor_result_match'
    
    findMeteors2(spath, dpath, dpathMatch, objTotalMatchNumber)

def processAllCCD2():
    
    
    dataRoot = "/data/gwac_data/gwac_orig_fits"
    dataDest = "/data/gwac_data/gwac_simot/meteor_181226"
    
    dateStrs = ['181213', '181214', '181215']
    for dateStr in dateStrs:
        spath0="%s/%s"%(dataRoot,dateStr)
        dpath0="%s/%s"%(dataDest,dateStr)
        if not os.path.exists(dpath0):
            os.system("mkdir %s"%(dpath0))
        
        ccds = os.listdir(spath0)
        for ccd in ccds:
            spath1="%s/%s"%(spath0,ccd)
            dpath1="%s/%s"%(dpath0,ccd)
            if not os.path.exists(dpath1):
                os.system("mkdir %s"%(dpath1))
    
            dpath2="%s/meteor_result"%(dpath1)
            dpath2m="%s/meteor_result_match"%(dpath1)
            objTotalMatchNumber = 0
            findMeteors2(spath1, dpath2, dpath2m, objTotalMatchNumber)

if __name__ == '__main__':
    
    processAllCCD2()
