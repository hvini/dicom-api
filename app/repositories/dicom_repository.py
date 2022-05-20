from app.repositories.instance_repository import InstancesRepo
from app.repositories.patient_repository import PatientsRepo
from app.repositories.study_repository import StudiesRepo
from app.repositories.serie_repository import SeriesRepo
from utils.dicom import getAllData, to3dArray, dcm2array
from fastapi.responses import JSONResponse
from fastapi import File, UploadFile
from sqlalchemy.orm import Session
from app import models, schemas
from pathlib import Path
from typing import List
import numpy as np
import json
import os

class DicomRepo:

    async def upload(db: Session, files: List[UploadFile] = File(...)):
        
        slices = getAllData(files=files)

        patientID = slices[0].PatientID
        patient = PatientsRepo.fetch_by_id(db, patientID)
        if (patient is None):
            patientName = str(slices[0].PatientName)
            patientBirthDate = slices[0].PatientBirthDate

            patient = await PatientsRepo.create(db=db, item=schemas.PatientsCreate(patientID=patientID, name=patientName, birthDate=patientBirthDate))

        studyInstanceUID = slices[0].StudyInstanceUID
        study = StudiesRepo.fetch_by_id(db, studyInstanceUID)
        if (study is None):
            studyDescription = slices[0].StudyDescription
            studyTime = slices[0].StudyTime

            study = await StudiesRepo.create(db=db, item=schemas.StudiesCreate(instanceUID=studyInstanceUID, patientID=patient.id, description=studyDescription, time=studyTime))

        seriesInstanceUID = slices[0].SeriesInstanceUID
        series = SeriesRepo.fetch_by_id(db, seriesInstanceUID)
        if (series is None):
            seriesDescription = slices[0].SeriesDescription

            series = await SeriesRepo.create(db=db, item=schemas.SeriesCreate(instanceUID=seriesInstanceUID, studyID=study.id, description=seriesDescription))
        
        InstancesRepo.delete_by_series_id(db=db, _id=series.id)

        destination = Path(f'./dicoms/{patient.patientID}/{study.instanceUID}/{series.instanceUID}')
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        for i, slice in enumerate(slices):
            filename = files[i].filename
            await InstancesRepo.create(db=db, item=schemas.InstancesCreate(seriesID=series.id, filename=filename))
            
            path = f'{destination}/{filename}'
            slice.save_as(path)

        return JSONResponse(status_code=201, content={'success': True, 'message': 'Files uploaded successfully'})

    async def get_3d_data(path: str):
        slices = getAllData(path=path)

        img2d = []
        for slice in slices:
            img2d.append(dcm2array(slice))

        img3d = to3dArray(img2d)

        data = img3d.ravel().tolist()

        dimX = img3d.shape[0]
        dimY = img3d.shape[1]
        dimZ = img3d.shape[2]
        pixelSpacing = slices[0].PixelSpacing[0]

        pos1a = slices[0].ImagePositionPatient[0]
        pos1b = slices[0].ImagePositionPatient[1]
        pos1c = slices[0].ImagePositionPatient[2]
        pos2a = slices[len(slices) - 1].ImagePositionPatient[0]
        pos2b = slices[len(slices) - 1].ImagePositionPatient[1]
        pos2c = slices[len(slices) - 1].ImagePositionPatient[2]
        
        data = {
            'data': data,
            'dimX': dimX,
            'dimY': dimY,
            'dimZ': dimZ,
            'pixelSpacing': pixelSpacing,
            'position1': {
                'a': pos1a,
                'b': pos1b,
                'c': pos1c
            },
            'position2': {
                'a': pos2a,
                'b': pos2b,
                'c': pos2c
            }
        }

        serialized_data = json.dumps(data)

        return JSONResponse(status_code=200, content=json.loads(serialized_data))

def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)