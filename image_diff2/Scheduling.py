# -*- coding: utf-8 -*-

from multiprocessing import Manager,Process,Lock
import time

def srcExtract(tpath, fname, fNumber, catList, astryQueue):
    
    isSuccess = True
    skyName = ''
    centerRa = 0
    centerDec = 0
    fwhm = 1.5
    starNum = 10000
    
    catList.append((fNumber, fname, isSuccess, skyName, centerRa, centerDec, fwhm, starNum))
    catQueue.put((fNumber, fname, isSuccess, skyName, centerRa, centerDec, fwhm, starNum))
    
def newSkyTemplate(tempMap, skyName):
    
    tempMap['skyName'] = 'tempPath'
    
def doAstrometry(catList, curCatIdx):

class BatchImageDiff(object):
    
    def __init__(self):
        self.dataMgr = Manager()
        self.catList = self.dataMgr.list()
        self.catQueue = self.dataMgr.Queue()
        self.tempMap = self.dataMgr.dict()
        self.curCatIdx = 0
    

def worker(d, key, value, lock):
    with lock:
        #d[key] = value
        d.append((key,value))
 
if __name__ == '__main__':
    lock=Lock()
    mgr = multiprocessing.Manager()
    d = mgr.list()
    jobs = [ multiprocessing.Process(target=worker, args=(d, i, i*2, lock))
             for i in range(10)
             ]
    for j in jobs:
        j.start()
    for j in jobs:
        j.join()
    print ('Results:' )
    #for key, value in enumerate(dict(d)):
    #    print("%s=%s" % (key, value))
    for sky in d:
        print(sky)