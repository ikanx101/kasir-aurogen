import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..database import get_db
from ..models import Event, MenuItem, Transaction, TransactionItem
from ..config import STRUK_DIR, CASHIER_PASSCODE
from ..utils.struk_gen import generate_struk
from ..templates_config import templates

router = APIRouter()

WIB = timezone(timedelta(hours=7))


class CartItem(BaseModel):
    menu_item_id: int
    qty: int


class CheckoutRequest(BaseModel):
    event_id: int
    items: List[CartItem]


@router.get("/kasir", response_class=HTMLResponse)
async def kasir_select(request: Request, db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.is_active == True).order_by(Event.start_date.desc()).all()
    passcode_required = bool(CASHIER_PASSCODE)
    return templates.TemplateResponse(
        "kasir/select_event.html",
        {"request": request, "events": events, "passcode_required": passcode_required},
    )


@router.get("/kasir/pos/{event_id}", response_class=HTMLResponse)
async def pos_page(request: Request, event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id, Event.is_active == True).first()
    if not event:
        return RedirectResponse("/kasir", status_code=302)
    items = db.query(MenuItem).filter(MenuItem.event_id == event_id).order_by(MenuItem.name).all()
    items_data = [{"id": i.id, "name": i.name, "price": i.price, "stock": i.stock} for i in items]
    return templates.TemplateResponse(
        "kasir/pos.html",
        {"request": request, "event": event, "items": items_data},
    )


@router.get("/api/events/{event_id}/menu-items")
async def get_menu_items(event_id: int, db: Session = Depends(get_db)):
    items = db.query(MenuItem).filter(MenuItem.event_id == event_id).order_by(MenuItem.name).all()
    return JSONResponse([
        {"id": i.id, "name": i.name, "price": i.price, "stock": i.stock}
        for i in items
    ])


@router.post("/api/transactions")
async def create_transaction(payload: CheckoutRequest, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == payload.event_id, Event.is_active == True).first()
    if not event:
        return JSONResponse({"error": "Event tidak ditemukan atau tidak aktif."}, status_code=400)

    if not payload.items:
        return JSONResponse({"error": "Keranjang kosong."}, status_code=400)

    # Validate stock and gather items
    resolved_items = []
    for cart_item in payload.items:
        menu_item = db.query(MenuItem).filter(MenuItem.id == cart_item.menu_item_id, MenuItem.event_id == payload.event_id).first()
        if not menu_item:
            return JSONResponse({"error": "Item tidak ditemukan."}, status_code=400)
        if menu_item.stock <= 0:
            return JSONResponse({"error": f"Stok {menu_item.name} habis."}, status_code=400)
        if cart_item.qty > menu_item.stock:
            return JSONResponse({"error": f"Stok {menu_item.name} tidak cukup. Tersedia: {menu_item.stock}."}, status_code=400)
        resolved_items.append((menu_item, cart_item.qty))

    total = sum(m.price * q for m, q in resolved_items)
    now_wib = datetime.now(WIB)

    # Nomor transaksi unik berbasis waktu + UUID (menghindari race condition)
    tx_suffix = uuid.uuid4().hex[:6].upper()
    tx_number = f"TRX-{now_wib.strftime('%Y%m%d')}-{tx_suffix}"

    # Create transaction
    tx = Transaction(
        event_id=payload.event_id,
        transaction_number=tx_number,
        created_at=now_wib.replace(tzinfo=None),
        total=total,
    )
    db.add(tx)
    db.flush()

    struk_items = []
    for menu_item, qty in resolved_items:
        subtotal = menu_item.price * qty
        tx_item = TransactionItem(
            transaction_id=tx.id,
            menu_item_id=menu_item.id,
            item_name=menu_item.name,
            item_price=menu_item.price,
            qty=qty,
            subtotal=subtotal,
        )
        db.add(tx_item)
        menu_item.stock -= qty
        struk_items.append({
            "name": menu_item.name,
            "qty": qty,
            "price": menu_item.price,
            "subtotal": subtotal,
        })

    # Generate struk PNG
    struk_filename = f"{tx_number}.png"
    struk_path = os.path.join(STRUK_DIR, struk_filename)
    struk_generated = False
    try:
        generate_struk(
            event_name=event.name,
            transaction_number=tx_number,
            items=struk_items,
            total=total,
            created_at=now_wib,
            output_path=struk_path,
        )
        tx.struk_path = struk_path
        struk_generated = True
    except Exception:
        pass

    db.commit()

    return JSONResponse({
        "success": True,
        "transaction_number": tx_number,
        "total": total,
        "struk_url": f"/struk/{struk_filename}" if struk_generated else None,
    })


@router.get("/struk/{filename}")
async def download_struk(filename: str):
    if not re.fullmatch(r'[A-Za-z0-9_\-]+\.png', filename):
        return JSONResponse({"error": "Invalid filename"}, status_code=400)
    path = os.path.join(STRUK_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(path, media_type="image/png", filename=filename)
