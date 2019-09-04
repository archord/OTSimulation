
#- Function 1: compress(flux)
def compressFluxValue(flux):
    '''------
       parameters:
            flux : matrix
       ------
       Return:
            a ndarray after the flux compressed
       '''
    import numpy as np
    frow,fcol = flux.shape[0], flux.shape[1]
    # The number of unmasked pixels
    N = (frow-1)*(fcol-1)
    # Row and columns of the compressed matrix
    crow = int(frow/2)
    ccol = int(fcol/2)
    # Return the compressed matrix
    compresse = list()
    for i in range(crow):
        tmp = list()
        for j in range(ccol):
            # Compressing the flux-value
            element = (flux[2*i,2*j]+flux[2*i,2*j+1]+flux[2*i+1,2*j]+flux[2*i+1,2*j+1])*1.0/N
            tmp.append(element)
        compresse.append(tmp)
    return np.asarray(compresse)

#- Function 2: rescaleFluxValue(compress)
def rescaleFluxValue(compress):
     '''--------
        parameters:
              compress : a ndarray which represent the flux-values after compressing
        --------
        Return:
              a ndarray which contains the flux-values rescaled
     '''
     
     import scipy as sp
     # Compute the median of the ndarray compress
     median = sp.median(compress)
     # The compress minus the median
     compressMinusMed = compress-median
     abs_median = sp.median(sp.absolute(compressMinusMed))
     if abs_median == 0:
         return [999999999]
     else:
         return compressMinusMed/(abs_median*1.4826)

 #- Function 3: bRescaleFluxValue(flux)
def bRescaleFluxValue(flux):
     '''--------
        description:
               An additional rescaling from Brink et al.
        --------
        parameters:
               flux : a ndarray
        --------
        Return:
               A ndarray which contains the flux-values rescaled
     '''
     import scipy as sp
     import numpy as np
     # Masked pixels are excluded from the computation of the median.Namely,moving the right-hand column and last row of flux.
     tflux = flux[:-1,:-1]
     return (flux-sp.median(tflux))/np.max(np.abs(flux))
 
