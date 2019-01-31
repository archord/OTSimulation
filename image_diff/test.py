# -*- coding: utf-8 -*-

import os

def getList(tpath, dirName, offset):
    
    fpath = "%s/%s"%(tpath, dirName)
    tdirs = os.listdir(fpath)
    tdirs.sort()
    
    print("total %d"%(len(tdirs)))
    tstr = ''
    for tfile in tdirs:
       tstr += ("%d,"%(int(tfile.split('.')[0])+offset))

    fp0 = open('%s.txt'%(dirName), 'w')
    fp0.write(tstr)
    fp0.close()
            
if __name__ == "__main__":
    
    dirName=['img10000Sel','img20000Sel','img30000Sel']
    tpath=r'E:\work\事物\04论文写作\暂现源深度学习\image\OT2 example'
    getList(tpath, dirName[0], 0)
    getList(tpath, dirName[1], 10000)
    getList(tpath, dirName[2], 20000)
