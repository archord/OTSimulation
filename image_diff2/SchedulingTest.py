# -*- coding: utf-8 -*-

import multiprocessing
from multiprocessing import Manager,Process,Lock
import time


def worker(d, d2, key, value, lock):
    with lock:
        d.append((key,value))
        d2[key]=value
 
if __name__ == '__main__':
    lock=Lock()
    mgr = multiprocessing.Manager()
    d = mgr.list()
    d2 = mgr.dict()
    jobs = [ multiprocessing.Process(target=worker, args=(d, d2, i, i*2, lock))
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
    print(d2)