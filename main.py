from typing import List
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

app = FastAPI()


@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    return {"filenames": [file.filename for file in files]}


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
