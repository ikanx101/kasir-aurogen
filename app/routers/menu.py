from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MenuItem, Event
from .auth import is_admin

router = APIRouter(prefix="/admin")


@router.post("/events/{event_id}/menu")
async def create_menu_item(
    request: Request,
    event_id: int,
    name: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    item = MenuItem(event_id=event_id, name=name, price=price, stock=stock)
    db.add(item)
    db.commit()
    return RedirectResponse(f"/admin/events/{event_id}", status_code=302)


@router.post("/menu/{item_id}/update")
async def update_menu_item(
    request: Request,
    item_id: int,
    name: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if item:
        item.name = name
        item.price = price
        item.stock = stock
        db.commit()
        return RedirectResponse(f"/admin/events/{item.event_id}", status_code=302)
    return RedirectResponse("/admin/events", status_code=302)


@router.post("/menu/{item_id}/delete")
async def delete_menu_item(
    request: Request,
    item_id: int,
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if item:
        event_id = item.event_id
        db.delete(item)
        db.commit()
        return RedirectResponse(f"/admin/events/{event_id}", status_code=302)
    return RedirectResponse("/admin/events", status_code=302)


@router.get("/api/events/{event_id}/menu-items")
async def get_menu_items_api(event_id: int, db: Session = Depends(get_db)):
    items = db.query(MenuItem).filter(MenuItem.event_id == event_id).all()
    return JSONResponse([
        {"id": i.id, "name": i.name, "price": i.price, "stock": i.stock}
        for i in items
    ])
