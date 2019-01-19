# -*- coding: utf-8 -*-
import numpy as np
from matplotlib import pyplot as plt


tdata = np.loadtxt("E:/mag.txt")

plt.hist(tdata,100)
plt.show()