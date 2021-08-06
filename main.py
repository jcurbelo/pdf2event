from io import BytesIO, FileIO
from typing import List
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from utils.pdf_parser import parse_files

templates = Jinja2Templates(directory="templates")

app = FastAPI()


@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    return {"result": parse_files([get_file_io(f) for f in files])}


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


# returns file-like object
def get_file_io(file: UploadFile):
    return BytesIO(file.file.read())
