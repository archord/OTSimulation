#- n2sig5; n3sig5; n2sig3; n3sig3
def nsig(rflux_d,fluxValue,pixelValue):
    '''-------
       parameters:
           rflux_d : A ndarray.Rescale cutout by calling function rescaleFluxValue."_d" represents the difference images.
           fluxValue : int.
           pixelValue: int.
       ------
       Return:
           a numeric.
    '''
    rows,cols = rflux_d.shape
    rcen = int(rows/2)
    ccen = int(cols/2)
    tmp = int((pixelValue+1)/2)
    nsig =  rflux_d[rcen-tmp:rcen+tmp+1,ccen-tmp:ccen+tmp+1]
    return nsig[nsig<-fluxValue].size

#- colmeds
def colmeds(brflux_d):
    '''-------
       description :
           The maximum of the median of each column on brflux_d.
       -------
       parameters :
           brflux_d : A ndarray.Rescale cutout by calling function bRescaleFluxValue."_d" represents the difference images.
       ------
       Return :
           a numeric.
    '''
    import numpy as np
    cols = brflux_d.shape[1]
    colmedmax = np.median(brflux_d[:,0])
    for i in range(cols-1):
        tmp = np.median(brflux_d[:,i+1])
        if tmp > colmedmax:
            colmedmax = tmp
    return colmedmax

#- diffsum
def diffsum(rflux_d):
    '''--------
       description :
            The sum of the matrix elements in a 5*5 element box centerd on the detection location on rflux_d.
       --------
       parameters :
            rflux_d : A ndarray.Rescale cutout by calling function rescaleFluxValue."_d" represents the difference images.
       -------
       Return :
            a numeric.
    '''
    import scipy as sp
    rows,cols = rflux_d.shape
    rcen = int(rows/2)
    ccen = int(cols/2)
    tmp = rflux_d[rcen-2:rcen+3,ccen-2:ccen+3]
    return sp.sum(tmp)

#- n2sig5shift; n3sig5shift; n2sig3shift; n3sig3shift
def nsigshift(rflux_d,rflux_t,fluxValue,pixelValue):
    '''--------
       parameters :
           rflux_d : A ndarray.Rescale cutout by calling function rescaleFluxValue. "_d" represents the difference images.
           rflux_t : A ndarray.Rescale cutout by calling function rescaleFluxValue. "_t" represents the template images.
           fluxValue : int.
           pixelValue : int.
       -------
       Return:
           a numeric.
    '''
    counts = (pixelValue+2)**2
    num_d = counts-nsig(rflux_d,-fluxValue,pixelValue)
    num_t = counts-nsig(rflux_t,-fluxValue,pixelValue)
    return num_d-num_t

#- numneg
def numneg(rflux_d):
    '''---------
       description :
           The number of negative matrix elements in a 7*7 element box centered on the detection in rflux_d.
       ---------
       parameters :
           rflux_d : A ndarray.Rescale cutout by calling function rescaleFluxValue. "_d" represents the difference images.
       ---------
       Return :
           a numeric.
    '''
    #import numpy as np
    rows,cols = rflux_d.shape
    rcen = int(rows/2)
    ccen = int(cols/2)
    # 7*7 matrix
    tmp = rflux_d[rcen-3:rcen+4,ccen-3:ccen+4]
    return tmp[tmp<0].size
