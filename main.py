from io import BytesIO, FileIO
from typing import List
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from utils.pdf_parser import parse_files
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.datastructures import Secret

config = Config('.env')  # read config from .env file
oauth = OAuth(config)
oauth.register(
    name='practice_panther',
    api_base_url='https://app.practicepanther.com/',
    authorize_url='https://app.practicepanther.com/Oauth/Authorize',
    scope='full'
)

templates = Jinja2Templates(directory="templates")


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=config(
    'SECRET_KEY', cast=Secret))


@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    return {"result": parse_files([get_file_io(f) for f in files])}


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/auth/login")
async def login_via_practice_panther(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.practice_panther.authorize_redirect(request, redirect_uri)


@app.route('/auth/callback')
async def auth(request: Request):
    token = await oauth.practice_panther.authorize_access_token(request)
    return {"token": token}

# returns file-like object


def get_file_io(file: UploadFile):
    return BytesIO(file.file.read())
