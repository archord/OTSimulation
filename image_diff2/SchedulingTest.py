# -*- coding: utf-8 -*-

import multiprocessing
from multiprocessing import Manager,Process,Lock,Queue
import time
import traceback


def addlist(flist, lock):
    for i in range(20):
        with lock:
            flist.append(len(flist))
        time.sleep(1)
        
def querylist(qqueue, flist, lock):
    for i in range(3):
        with lock:
            qqueue.put(len(flist))
            time.sleep(5)
            
            
def testRunning(flist, isrunning):
    
    for i in range(5):
        isrunning.value = 1
        time.sleep(3)
        flist.append(len(flist))
        isrunning.value = 0
        time.sleep(3)
 
if __name__ == '__main__':
    lock=Lock()
    mgr = multiprocessing.Manager()
    fileList = mgr.list()
    queryQueue = mgr.Queue()
    d2 = mgr.dict()
    
    fileList2 = mgr.list()
    fileList2.append(-1)
    trunning = mgr.Value('i', 0)
    
    job1 = multiprocessing.Process(target=addlist, args=(fileList, lock))
    job1.start()
    
    job2 = multiprocessing.Process(target=querylist, args=(queryQueue, fileList, lock))
    job2.start()
    
    job3 = multiprocessing.Process(target=testRunning, args=(fileList2, trunning))
    job3.start()
    
    time.sleep(0.5)
    for i in range(60):
        fsize = len(fileList)
        try:
            print("%d,%d:%d"%(fsize, fileList[fsize-1], queryQueue.get(False,0.1)))
        except Exception as e:
            print("%d error"%(i))
            #print(e)
            #tstr = traceback.format_exc()
            #print(tstr)
        
        fsize = len(fileList2)
        if trunning.value == 0:
            print("job3 is not running: %d,%d"%(fsize, fileList2[fsize-1]))
        else:
            print("job3 is running: %d,%d"%(fsize, fileList2[fsize-1]))
            
        time.sleep(1)
        
    
    print("here1")
    job1.join()
    job2.join()
    job3.join()
    print("here2")
