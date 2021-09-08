from io import BytesIO
from typing import List, Tuple
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from utils.pdf_parser import parse_files
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.datastructures import Secret
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

config = Config(".env")  # read config from .env file
oauth = OAuth(config)
oauth.register(
    name="practice_panther",
    api_base_url="https://app.practicepanther.com/",
    authorize_url="https://app.practicepanther.com/oauth/authorize",
    access_token_url="https://app.practicepanther.com/oauth/token",
    scope="full"
)


templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=config(
    "SECRET_KEY", cast=Secret))


@app.get("/matters")
async def get_matters(request: Request, search_text: str = None):
    oauth_values = request.session.get("oauth_values", {})
    params = {
        "status": "Open",
    }
    if search_text:
        params["search_text"] = search_text
    resp = await oauth.practice_panther.get("/api/v2/matters",
                                            params=params,
                                            timeout=None,
                                            token=oauth_values)
    matters = resp.json()

    return {"result": matters[:20]}


@app.get("/users")
async def get_matters(request: Request, email_address: str = None):
    oauth_values = request.session.get("oauth_values", {})
    params = {
    }
    if email_address:
        params["email_address"] = email_address
    resp = await oauth.practice_panther.get("/api/v2/users",
                                            params=params,
                                            timeout=None,
                                            token=oauth_values)
    return {"result": resp.json()}


@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    return {"result": parse_files([get_file_io(f) for f in files])}


@app.post("/generate-events")
async def generate_events(request: Request, cases: List[dict]):
    oauth_values = request.session.get("oauth_values", {})
    results = []
    for case in cases:
        matter_ref = case["matter_ref"]
        users = case["assigned_to_users"]
        for event in case["events"]:
            for date in event["dates"]:
                payload = {
                    "subject": "DEADLINE - " + event["name"],
                    "is_all_day": True,
                    "start_date_time": date["value"] + "T07:00:00Z",
                    "end_date_time": date["value"] + "T07:30:00Z",
                    "matter_ref": {
                        "id": matter_ref["id"]
                    },
                    "assigned_to_users": users,
                    "tags": [
                        "PDF2Event",
                    ]
                }
                resp = await oauth.practice_panther.post("/api/v2/events", json=payload, token=oauth_values)
                results.append(resp.json())

    return {"result": results}


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/auth/login")
async def login_via_practice_panther(request: Request):
    # HACK: This is a hack to get the auth callback URL with https.
    # redirect_uri = request.url_for("auth")
    redirect_uri = "https://pdf2event.com/auth/callback"
    return await oauth.practice_panther.authorize_redirect(request, redirect_uri)


@app.route("/auth/callback")
async def auth(request: Request):
    try:
        resp = await oauth.practice_panther.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f"<h1>{error.error}</h1>")
    oauth_values = {
        "access_token": resp["access_token"],
        "refresh_token": resp["refresh_token"],
        "expires_in": resp["expires_in"],
        "expires_at": resp["expires_at"],
        "token_type": resp["token_type"],
    }
    request.session["oauth_values"] = oauth_values
    return RedirectResponse(url="/")


@app.get("/auth/logout")
async def logout(request: Request):
    request.session.pop("oauth_values", None)
    return RedirectResponse(url="/")

# returns file-like object


def get_file_io(file: UploadFile) -> Tuple[BytesIO, str]:
    return (BytesIO(file.file.read()), file.filename)
