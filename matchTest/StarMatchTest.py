# -*- coding: utf-8 -*-
import numpy as np
from scipy.spatial import KDTree
import matplotlib.pyplot as plt
from datetime import datetime
from blindmatch import BlindMatch


def test():
    
    tpath = 'data'
    #tfile1 = 'G031_mon_objt_190116T21430226.cat'
    #tfile2 = 'G041_mon_objt_190101T21551991.cat'
    tfile1 = 'G041_mon_objt_181018T17592546.cat'
    tfile2 = 'G021_mon_objt_181101T17255569.cat'
    
    doAll(tpath, tfile1, tfile2)
    
if __name__ == "__main__":
        
    test()