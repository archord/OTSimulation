# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

    
def loadData(path):
    
    tnames = ["ID1", "ID2", "ra", "dec", "d1", "d2", "d3", "d4", "d5"]
    
    datas = pd.read_csv(path,header=None, delim_whitespace=True, names=tnames)
    
    datas['ID1'] = datas['ID1'].astype(np.int)
    datas['ID2'] = datas['ID2'].astype(np.int)
    
    return datas
    
if __name__ == '__main__':

    tpath = 'test.dat'
    datas = loadData(tpath)
    
    datas2 = datas.groupby(['ID1', 'ID2'])['d1'].count()
    #datas2 = datas.set_index(['ID1', 'ID2'])
    uniqueIds = np.unique(datas2.index.values)
    print(uniqueIds)
    for tid in uniqueIds:
        print(tid)
        d1 = datas[(datas.ID1==tid[0]) & (datas.ID2==tid[1])].d1.values
        d1.sort()
        print(d1)
        plt.plot(d1,'*-')
        plt.show()
        break
    
    