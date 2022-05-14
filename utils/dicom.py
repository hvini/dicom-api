from pydicom.filereader import dcmread
from pathlib import Path
import numpy

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
    img_shape = list(slices[0].pixel_array.shape)
    img_shape.append(len(slices))
    img3d = numpy.zeros(img_shape)

    # add the 3d image data to new array
    for i, s in enumerate(slices):

        img2d = s.pixel_array
        img3d[:, :, i] = img2d

    return img3d