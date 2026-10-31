from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import quote

from app.auth import get_current_user
from app.config import BASE_DIR
from app.storage.manager import get_storage_backend

router = APIRouter(prefix="/skydrive", tags=["skydrive"])
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

@router.get("", response_class=HTMLResponse)
async def skydrive_dashboard(request: Request, folder: str = "root", name: str = ""):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")

    storage, backend_name = get_storage_backend()
    items = storage.list_items(user["email"], parent_folder_id=folder)

    folder_name = name or ("SkyDrive" if folder == "root" else folder)

    return templates.TemplateResponse(request=request, name="skydrive.html", context={
        "current_user": user,
        "items": items,
        "current_folder": folder,
        "current_folder_name": folder_name,
        "backend_name": backend_name
    })

@router.post("/folder/create")
async def create_folder(
    request: Request,
    folder_name: str = Form(...),
    parent_folder: str = Form("root")
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")

    storage, _ = get_storage_backend()
    storage.create_folder(user["email"], folder_name=folder_name, parent_folder_id=parent_folder)
    return RedirectResponse(url=f"/skydrive?folder={quote(parent_folder)}", status_code=303)

@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    parent_folder: str = Form("root")
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")

    storage, _ = get_storage_backend()
    storage.upload_file(
        user_email=user["email"],
        file_name=file.filename,
        file_stream=file.file,
        mime_type=file.content_type,
        parent_folder_id=parent_folder
    )
    return RedirectResponse(url=f"/skydrive?folder={quote(parent_folder)}", status_code=303)

@router.get("/download")
async def download_file(request: Request, file_id: str):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")

    storage, _ = get_storage_backend()
    result = storage.get_file(user["email"], file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File non trovato")

    stream, filename, mime_type = result
    encoded_filename = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
    }
    return StreamingResponse(stream, media_type=mime_type, headers=headers)

@router.post("/delete")
async def delete_item(
    request: Request,
    item_id: str = Form(...),
    parent_folder: str = Form("root")
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/auth/login")

    storage, _ = get_storage_backend()
    storage.delete_item(user["email"], item_id)
    return RedirectResponse(url=f"/skydrive?folder={quote(parent_folder)}", status_code=303)
