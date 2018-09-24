# -*- coding: utf-8 -*-

import os

if __name__ == "__main__":
    
    tpath = r'F:\gwac_data\chaodata_view\chaodata_view_bad'
    flist = os.listdir(tpath)
    flist.sort()
    
    imgs = []
    for tfilename in flist:
        print(tfilename)