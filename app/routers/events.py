import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..models import Event, MenuItem
from .auth import is_admin
from ..templates_config import templates

router = APIRouter(prefix="/admin")


@router.get("/events", response_class=HTMLResponse)
async def list_events(request: Request, db: Session = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    events = db.query(Event).order_by(Event.start_date.desc()).all()
    return templates.TemplateResponse("admin/events.html", {"request": request, "events": events})


@router.post("/events")
async def create_event(
    request: Request,
    name: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    event = Event(name=name, start_date=start_date, end_date=end_date, is_active=False)
    db.add(event)
    db.commit()
    return RedirectResponse("/admin/events", status_code=302)


@router.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail(request: Request, event_id: int, db: Session = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return RedirectResponse("/admin/events", status_code=302)
    items = db.query(MenuItem).filter(MenuItem.event_id == event_id).all()
    return templates.TemplateResponse(
        "admin/event_detail.html",
        {"request": request, "event": event, "items": items},
    )


@router.post("/events/{event_id}/update")
async def update_event(
    request: Request,
    event_id: int,
    name: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        event.name = name
        event.start_date = start_date
        event.end_date = end_date
        db.commit()
    return RedirectResponse(f"/admin/events/{event_id}", status_code=302)


@router.post("/events/{event_id}/toggle-active")
async def toggle_active(request: Request, event_id: int, db: Session = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        event.is_active = not event.is_active
        db.commit()
    return RedirectResponse("/admin/events", status_code=302)


@router.post("/events/{event_id}/delete")
async def delete_event(request: Request, event_id: int, db: Session = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    event = db.query(Event).filter(Event.id == event_id).first()
    if event:
        # Bersihkan file PNG struk sebelum hapus data
        for tx in event.transactions:
            if tx.struk_path and os.path.exists(tx.struk_path):
                try:
                    os.remove(tx.struk_path)
                except Exception:
                    pass
        db.delete(event)
        db.commit()
    return RedirectResponse("/admin/events", status_code=302)
