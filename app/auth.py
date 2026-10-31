from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional

from app.database import (
    create_user, authenticate_user, create_session,
    get_user_by_session, delete_session
)
from app.config import COOKIE_NAME, BASE_DIR

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

def get_current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return get_user_by_session(token)

def require_user(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/auth/login"})
    return user

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url="/skydrive")
    return templates.TemplateResponse(request=request, name="login.html", context={
        "current_user": None,
        "is_register": False,
        "error": None
    })

@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    clean_user = username.strip()
    user = authenticate_user(clean_user, password)
    if not user:
        return templates.TemplateResponse(request=request, name="login.html", context={
            "current_user": None,
            "is_register": False,
            "error": "Windows Live ID o password non corretti. Ricorda di inserire l'indirizzo completo (es. stefano@live.it)."
        }, status_code=400)

    token = create_session(user["id"])
    response = RedirectResponse(url="/skydrive", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 30, # 30 days
        samesite="lax"
    )
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url="/skydrive")
    return templates.TemplateResponse(request=request, name="login.html", context={
        "current_user": None,
        "is_register": True,
        "error": None
    })

@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    domain: str = Form("@live.it"),
    first_name: str = Form(""),
    last_name: str = Form(""),
    birth_date: str = Form("1995-01-01"),
    gender: str = Form("m"),
    forward_email: str = Form(""),
):
    clean_user = username.strip().lower()
    if "@" in clean_user:
        email = clean_user
    else:
        email = f"{clean_user}{domain}"

    display_name = f"{first_name} {last_name}".strip() or clean_user.split('@')[0]
    user = create_user(
        email=email,
        password=password,
        display_name=display_name,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        gender=gender,
        forward_email=forward_email
    )
    if not user:
        return templates.TemplateResponse(request=request, name="login.html", context={
            "current_user": None,
            "is_register": True,
            "error": f"L'indirizzo {email} è già registrato. Scegline un altro."
        }, status_code=400)

    token = create_session(user["id"])
    response = RedirectResponse(url="/skydrive", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 30,
        samesite="lax"
    )
    return response

@router.get("/logout")
async def logout(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        delete_session(token)
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
