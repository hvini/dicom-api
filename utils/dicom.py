from pydicom.filereader import dcmread
from pathlib import Path
import numpy as np

def getAllData(files=None, path=None):
    slices = []
    if (files is None):
        directory = Path(path)
        dicom_list = list(directory.glob('*.dcm'))
        for dicom in dicom_list:
            slices.append(read(dicom))
    else:
        for file in files:
            slices.append(read(file.file))

    return slices

def read(dicom):
    return dcmread(dicom)

def to3dArray(slices):

    # create a new array of zeros with the same dimensions as the first slice
    img_shape = list(slices[0].shape)
    img_shape.append(len(slices))
    img3d = np.zeros(img_shape)

    # add the 3d image data to new array
    for i, s in enumerate(slices):

        img2d = s
        img3d[:, :, i] = img2d

    return img3d

def dcm2array(dcm):
    """Converts the raw pixel array in dicom data to an image array in HU units.
    Args:
        dcm (dicom.dataset.FileDataset): input dicom data.
    
    Returns:
        Image array in HU units.
    """
    exception_template = "An exception of type {0} occurred. Arguments:\n{1!r}"

    # Apparently pydicom is already taking into consideration
    # the PixelRepresentation and BitsAllocated when making the pixel_array.
    # However is not considering BitsStored nor HighBit.
    array = dcm.pixel_array

    # These are Type 1 so they shouldn't raise an error
    slope = dcm.RescaleSlope
    intercept = dcm.RescaleIntercept
    representation = dcm.PixelRepresentation

    # This is Type 3, so it might not be present in the dicom file
    try:
        padding = dcm.PixelPaddingValue
    except AttributeError as ex:
        padding = None

    # Determination of proper pixel padding value
    if isinstance(padding, int) and padding > 32767 and representation == 1:
        padding = padding.to_bytes(2, byteorder='little', signed=False)

    if isinstance(padding, bytes):
        padding = int.from_bytes(padding, byteorder='little', signed=(representation == 1))
    
    # Set padded area to air (HU=-1000)
    if padding is not None:
        array[array == padding] = -1000 - intercept

    # Safety measure
    # There a few cases in which the pixel padding value is valid
    # but does not correspond with the actual padded values in the data (< -1000).
    # Furthermore, CT is represented at most with 12 bits, thus it cannot exceed 4095.
    array[array <= -1000] = -1000 - intercept
    array[array > 4095] = 4095

    # Transform to Hounsfield Units.
    array = np.float64(array)
    array *= slope
    array += intercept
    array = np.int16(array)

    return array