from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import ADMIN_PASSWORD
from ..templates_config import templates

router = APIRouter()


def is_admin(request: Request) -> bool:
    return request.session.get("is_admin", False)


def require_admin(request: Request):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    return None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_admin(request):
        return RedirectResponse("/admin/events", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse("/admin/events", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Password salah."})


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
