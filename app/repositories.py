from sqlalchemy.orm import Session
from . import models, schemas
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse
from typing import List
from utils.dicom import getAllData, to3dArray
import shutil
import os

class SeriesRepo:

    async def create(db: Session, item: schemas.SeriesCreate):
        db_item = models.Series(instanceUID=item.instanceUID, studyID=item.studyID, description=item.description)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        return db_item

    def fetch_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Series).offset(skip).limit(limit).all()

    def fetch_by_id(db: Session, _id):
        return db.query(models.Series).filter(models.Series.instanceUID == _id).first()

class InstancesRepo:
    
        async def create(db: Session, item: schemas.InstancesCreate):
            db_item = models.Instances(seriesID=item.seriesID, filename=item.filename)
            db.add(db_item)
            db.commit()
            db.refresh(db_item)

            return db_item

        def fetch_all(db: Session, skip: int = 0, limit: int = 100):
            return db.query(models.Instances).offset(skip).limit(limit).all()

        def delete_by_series_id(db: Session, _id):
            db.query(models.Instances).filter(models.Instances.seriesID == _id).delete()

class UploadRepo:

    async def upload(db: Session, files: List[UploadFile] = File(...)):
        
        slices = getAllData(files)

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
        for file in files:
            await InstancesRepo.create(db=db, item=schemas.InstancesCreate(seriesID=series.id, filename=file.filename))
            
            with open(destination + file.filename, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        return JSONResponse(status_code=201, content={'success': True, 'message': 'Files uploaded successfully'})

class StudiesRepo:

    async def create(db: Session, item: schemas.StudiesCreate):
        db_item = models.Studies(instanceUID=item.instanceUID, patientID=item.patientID, description=item.description, time=item.time)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        return db_item

    def fetch_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Studies).offset(skip).limit(limit).all()

    def fetch_by_id(db: Session, _id):
        return db.query(models.Studies).filter(models.Studies.instanceUID == _id).first()

class PatientsRepo:

    async def create(db: Session, item: schemas.PatientsCreate):
        db_item = models.Patients(patientID=item.patientID, name=item.name, birthDate=item.birthDate)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        return db_item

    def fetch_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Patients).offset(skip).limit(limit).all()

    def fetch_by_id(db: Session, _id):
        return db.query(models.Patients).filter(models.Patients.patientID == _id).first()