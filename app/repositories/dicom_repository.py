from app.repositories.instance_repository import InstancesRepo
from app.repositories.patient_repository import PatientsRepo
from app.repositories.study_repository import StudiesRepo
from app.repositories.serie_repository import SeriesRepo
from fastapi.responses import JSONResponse
from fastapi import File, UploadFile
from utils.dicom import getAllData
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

        destination = Path(f'./dicoms/{patient.patientID}/{study.instanceUID}/{seriesInstanceUID}')
        if (series is None):
            seriesDescription = slices[0].SeriesDescription

            series = await SeriesRepo.create(db=db, item=schemas.SeriesCreate(instanceUID=seriesInstanceUID, studyID=study.id, filepath=str(destination), description=seriesDescription))
        
        isExists = os.path.exists(destination)
        if not isExists:
            os.makedirs(destination)

        InstancesRepo.delete_by_series_id(db=db, _id=series.id)
        for i, slice in enumerate(slices):
            filename = files[i].filename
            await InstancesRepo.create(db=db, item=schemas.InstancesCreate(seriesID=series.id, filename=filename))
            
            path = f'{destination}/{filename}'
            slice.save_as(path)

        return JSONResponse(status_code=201, content={'success': True, 'message': 'Files uploaded successfully'})