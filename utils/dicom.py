from pydicom.filereader import dcmread
import multiprocessing
import numpy

def getAllData(files):
        
        # loop through all the files read them and store them in a list
        no_process = 3
        slices = []
        with multiprocessing.Pool(processes = no_process) as p:
            slices = p.map(read, files)

        return slices

def read(dicom):
    return dcmread(dicom.file)

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