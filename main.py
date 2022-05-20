from app.repositories.instance_repository import InstancesRepo
from app.repositories.instance_repository import InstancesRepo
from fastapi import Depends, FastAPI, File, UploadFile, Form
from app.repositories.patient_repository import PatientsRepo
from app.repositories.study_repository import StudiesRepo
from app.repositories.serie_repository import SeriesRepo
from app.repositories.dicom_repository import DicomRepo
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from db import get_db, engine
import app.models as models
from typing import List
import asyncio
import uvicorn

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.exception_handler(Exception)
def validation_exception_handler(request, err):
    return JSONResponse(status_code=500, content=jsonable_encoder({"code": "internal_error", "message": str(err)}))

### DICOMS ###
@app.post('/dicom/upload', tags=["Dicoms"])
async def upload_dicom(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    return await DicomRepo.upload(db=db, files=files)

@app.get('/dicom/3d', tags=["Dicoms"])
async def get_3d_data(path: str):
    return await DicomRepo.get_3d_data(path=path)

### PATIENTS ###
@app.get('/patients', tags=["Patients"])
def get_patients(db: Session = Depends(get_db)):
    return PatientsRepo.fetch_all(db=db)

@app.get('/patients/{id}/studies', tags=["Patients"])
def get_patient_studies(id: int, db: Session = Depends(get_db)):
    return PatientsRepo.fetch_patient_studies(db=db, _id=id)

### STUDIES ###
@app.get('/studies', tags=["Studies"])
def get_studies(db: Session = Depends(get_db)):
    return StudiesRepo.fetch_all(db=db)

@app.get('/studies/{id}/series', tags=["Studies"])
def get_study_series(id: int, db: Session = Depends(get_db)):
    return StudiesRepo.fetch_study_series(db=db, _id=id)

### SERIES ###
@app.get('/series', tags=["Series"])
def get_series(db: Session = Depends(get_db)):
    return SeriesRepo.fetch_all(db=db)

@app.get('/series/{id}/instances', tags=["Series"])
def get_series_instances(id: int, db: Session = Depends(get_db)):
    return SeriesRepo.fetch_serie_instances(db=db, _id=id)

### INSTANCES ###
@app.get('/instances', tags=["Instances"])
def get_instances(db: Session = Depends(get_db)):
    return InstancesRepo.fetch_all(db=db)

if __name__ == "__main__":
    uvicorn.run("main:app", port=3000, reload=True)