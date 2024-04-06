
# 示例代码
import numpy as np
from PIL import Image
from astropy.io import fits
import struct


def test1():
    binPath = "test/flat_red.bin"

    binData = np.fromfile(binPath, dtype='uint16')
    timg = np.reshape(binData, (2048,2048))
    hdu = fits.PrimaryHDU(timg)
    hdul = fits.HDUList([hdu])
    hdul.writeto("flat_red.fits")

    print(binData.shape)
    print(timg.shape)
    print(timg[0][0])
    print("max", np.max(timg))
    print("min", np.min(timg))
    print("average", np.average(timg))
    # hdu = fits.PrimaryHDU(timg)
    # hdul = fits.HDUList([hdu])
    # hdul.writeto("flat_red.fits")
    # Image.fromarray(timg).save("abc.png")



def test2():
    binPath = "test/flat_red.bin"

    width=2048
    height=2048

    raw=open(binPath,'rb')
    binarr = raw.read(width*height*2)
    raw.close()
    
    formateStr = '<%dH'%(width*height)
    print(formateStr)
    pixtuple = struct.unpack(formateStr,binarr[0:width*height*2])
    
    binData = np.array(pixtuple, dtype='uint16')
    timg = np.reshape(binData, (width,height))
    hdu = fits.PrimaryHDU(timg)
    hdul = fits.HDUList([hdu])
    hdul.writeto("test/flat_red_<.fits")

    print(binData.shape)
    print(timg.shape)
    print(timg[0][0])
    print("max", np.max(timg))
    print("min", np.min(timg))
    print("average", np.average(timg))
    # hdu = fits.PrimaryHDU(timg)
    # hdul = fits.HDUList([hdu])
    # hdul.writeto("flat_red.fits")
    # Image.fromarray(timg).save("abc.png")



test2()