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