# -*- coding: utf-8 -*-
import os
import traceback
import time
from PIL import Image
import requests
from datetime import datetime, timedelta
from gwac_util import getFullThumbnail
        
def batch(root):
    
    try:

        files = os.listdir(root)
        files.sort()
        for tfile in files:
            if tfile>='G022_mon_objt_190217T10501704.fit.fz' and tfile <='G022_mon_objt_190217T11294704.fit.fz':
                print(tfile)
                timg = getFullThumbnail(root, tfile, zoomFraction=1.0)
                dpath32 = "tmpImg/%s.jpg"%(tfile.split('.')[0])
                Image.fromarray(timg).save(dpath32,optimize=True,quality=30) #30 70=default
                break
                
    except Exception as e:
        print(str(e))
        traceback.print_exception()
        
if __name__ == '__main__':
    
    root = '/data/gwac_data/gwac_orig_fits/190217/G002_022'
    batch(root)
