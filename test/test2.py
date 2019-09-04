# -*- coding: utf-8 -*-
import numpy as np
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt



if __name__ == '__main__':
    
    dataFile = 'e:/resource/track_706658.txt'
   
    tdatas = np.loadtxt(dataFile, dtype='str')
    print(tdatas.shape)
    
    tdata0 = tdatas[0]
    dateStr0 = "%s %s"%(tdata0[0], tdata0[1])
    ttime0 = datetime.strptime(dateStr0, "%Y-%m-%d %H:%M:%S.%f")
    
    records = []
    for i, tdata in enumerate(tdatas):
        #if i>0:
            mag = float(tdata[2])
            dateStr1 = "%s %s"%(tdata[0], tdata[1])
            ttime1 = datetime.strptime(dateStr1, "%Y-%m-%d %H:%M:%S.%f")
            timeDiff = ttime1 - ttime0
            remainSeconds = timeDiff.seconds + timeDiff.microseconds/1000000.0
            records.append((remainSeconds, mag))
    
    records = np.array(records)
    np.savetxt("e:/resource/obj_records1.txt",records, fmt='%.2f',delimiter=',')