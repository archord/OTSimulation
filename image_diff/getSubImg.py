# -*- coding: utf-8 -*-
import os
  
if __name__ == "__main__":
    
    tpath1 = "/data/work/diff_img/20190116"
    dpath1 = "/data/work/diff_img/20190116tot"
    dpath2 = "/data/work/diff_img/20190116bad"
    
    if not os.path.exists(dpath1):
        os.system("mkdir -p %s"%(dpath1))
    if not os.path.exists(dpath2):
        os.system("mkdir -p %s"%(dpath2))
    
    dirs = os.listdir(tpath1)
    dirs.sort()
    
    for tdir in dirs:
        
        tpath2 = "%s/%s/subImg"%(tpath1, tdir)
        
        flist = os.listdir(tpath2)
        flist.sort()
        badImg2s = []
        fotImgs = []
        for tfilename in flist:
            if tfilename.find("badimg.npz")>-1:
                badImg2s.append(tfilename)
            elif tfilename.find("totimg")>-1:
                fotImgs.append(tfilename)
        
        badNum = len(badImg2s)
        fotNum = len(fotImgs)
        for i, tfilename in enumerate(badImg2s):
            if i%20==1:
                print(tfilename)
                os.system("cp %s/%s %s/%s"%(tpath2, tfilename, dpath2, tfilename))
        for i, tfilename in enumerate(fotImgs):
            print(tfilename)
            os.system("cp %s/%s %s/%s"%(tpath2, tfilename, dpath1, tfilename))