from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

from .database import engine, Base
from .models import Event, MenuItem, Transaction, TransactionItem
from .config import SECRET_KEY
from .routers import auth, events, menu, pos, admin
from .templates_config import templates

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kasir Dapoerasatoe")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=86400)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(menu.router)
app.include_router(pos.router)
app.include_router(admin.router)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}
