from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.database import init_db
from app.auth import router as auth_router, get_current_user
from app.skydrive.routes import router as skydrive_router
from app.passport.routes import router as passport_router
from app.spaces.routes import router as spaces_router

app = FastAPI(title="ReLive — Windows Live Revival Server", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

# Include routers
app.include_router(auth_router)
app.include_router(skydrive_router)
app.include_router(passport_router)
app.include_router(spaces_router)

@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    host = request.headers.get("host", "")
    line = f"{request.method} {request.url} (Host: {host})\n"
    print(f"--> [HTTP] {line.strip()}")
    try:
        log_file = BASE_DIR / "http_requests.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{request.client.host if request.client else 'local'}] {line}")
    except Exception:
        pass
    response = await call_next(request)
    return response

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def portal_home(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(request=request, name="portal.html", context={
        "current_user": user,
        "error": None
    })

@app.get("/download/configura-client.bat")
async def download_client_script():
    bat_file = BASE_DIR / "Configura_Client.bat"
    return FileResponse(
        path=str(bat_file),
        media_type="application/octet-stream",
        filename="Configura_Client.bat"
    )

@app.get("/mail", response_class=HTMLResponse)
async def mail_preview(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(request=request, name="base.html", context={
        "current_user": user,
        "service_name": "Mail",
        "content": """
        <div class="wl-main-content">
            <div style="background:white; border:1px solid #c8d9e8; border-radius:6px; padding:24px; max-width:700px; margin:20px auto;">
                <h2 style="color:#0072c6; margin-bottom:12px;">Windows Live Mail (DeltaSync)</h2>
                <p style="margin-bottom:10px;">Questo modulo sincronizzerà la posta del tuo account <strong>@live.it</strong> direttamente con il client desktop di <strong>Windows Live Mail</strong>.</p>
                <div style="background:#eef5fb; padding:12px; border-left:4px solid #0072c6; margin:16px 0; font-size:12px;">
                    <strong>Stato Server DeltaSync:</strong> In configurazione (endpoint <code>/DeltaSync_v2.0.0/Settings.aspx</code>).
                </div>
                <a href="/skydrive" class="wl-btn wl-btn-primary">Torna a SkyDrive</a>
            </div>
        </div>
        """
    })

@app.get("/writer", response_class=HTMLResponse)
async def writer_preview(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(request=request, name="base.html", context={
        "current_user": user,
        "service_name": "Writer",
        "content": """
        <div class="wl-main-content">
            <div style="background:white; border:1px solid #c8d9e8; border-radius:6px; padding:24px; max-width:700px; margin:20px auto;">
                <h2 style="color:#0072c6; margin-bottom:12px;">Windows Live Writer (MetaWeblog API)</h2>
                <p style="margin-bottom:10px;">L'editor blog desktop si collegherà a questo server revival. Tutte le immagini incollate nei post verranno archiviate automaticamente sul tuo <strong>SkyDrive / Google Drive</strong>.</p>
                <div style="background:#eef5fb; padding:12px; border-left:4px solid #0072c6; margin:16px 0; font-size:12px;">
                    <strong>Endpoint XML-RPC:</strong> <code>/xmlrpc</code> con Really Simple Discovery su <code>/rsd.xml</code>.
                </div>
                <a href="/skydrive" class="wl-btn wl-btn-primary">Torna a SkyDrive</a>
            </div>
        </div>
        """
    })

@app.get("/photos", response_class=HTMLResponse)
async def photos_preview(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(request=request, name="base.html", context={
        "current_user": user,
        "service_name": "Raccolta foto",
        "content": """
        <div class="wl-main-content">
            <div style="background:white; border:1px solid #c8d9e8; border-radius:6px; padding:24px; max-width:700px; margin:20px auto;">
                <h2 style="color:#0072c6; margin-bottom:12px;">Windows Live Raccolta Foto</h2>
                <p style="margin-bottom:10px;">Permette il caricamento e la condivisione diretta di album fotografici sincronizzati su <strong>SkyDrive (Google Drive)</strong> tramite il plugin di pubblicazione ufficiale.</p>
                <a href="/skydrive" class="wl-btn wl-btn-primary">Torna a SkyDrive</a>
            </div>
        </div>
        """
    })

@app.get("/0f000live/{target:path}")
async def glive_redirect(target: str, request: Request):
    """
    g.live.com link redirector handler.
    Windows Live applications query g.live.com to discover live spaces and verify network access.
    """
    host = request.headers.get("host", "")
    print(f"[*] g.live.com redirect query: /0f000live/{target} from {host}")
    # Redirect to spaces.live.com or return 200 OK
    return RedirectResponse(url="http://spaces.live.com/default.aspx", status_code=302)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"])
async def catch_all_fallback(full_path: str, request: Request):
    """
    Catch-all fallback route for unhandled client queries.
    Returns 200 OK so that ancillary XML/JSON/REST probes succeed cleanly.
    """
    host = request.headers.get("host", "")
    print(f"[*] Catch-all fallback invoked for: {request.method} {full_path} (Host: {host})")
    return Response(
        content="<?xml version=\"1.0\" encoding=\"utf-8\"?><Response><Status>OK</Status></Response>",
        media_type="text/xml; charset=utf-8",
        status_code=200
    )
