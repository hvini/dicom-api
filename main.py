from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.repositories import UploadRepo
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

@app.post('/upload', tags=["Upload"])
async def upload_dicom(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    return await UploadRepo.upload(db=db, files=files)

if __name__ == "__main__":
    uvicorn.run("main:app", port=3000, reload=True)