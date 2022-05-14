from app.repositories.instance_repository import InstancesRepo
from app.repositories.patient_repository import PatientsRepo
from app.repositories.study_repository import StudiesRepo
from app.repositories.serie_repository import SeriesRepo
from utils.dicom import getAllData, to3dArray
from fastapi.responses import JSONResponse
from fastapi import File, UploadFile
from sqlalchemy.orm import Session
from app import models, schemas
from typing import List
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

        destination = f'./dicoms/{patient.patientID}/{study.instanceUID}/{series.instanceUID}/'
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        for i, slice in enumerate(slices):    
            filename = files[i].filename
            await InstancesRepo.create(db=db, item=schemas.InstancesCreate(seriesID=series.id, filename=filename))
            
            destination = destination + filename
            with open(destination, "wb") as buffer:
                slice.save_as(buffer)

        return JSONResponse(status_code=201, content={'success': True, 'message': 'Files uploaded successfully'})

    async def get_3d_data(path: str):
        slices = getAllData(path=path)
        img3d = to3dArray(slices)

        data = img3d.ravel().tolist()
        rounded_data = [round(x) for x in data]

        return JSONResponse(status_code=200, content={'data': rounded_data})