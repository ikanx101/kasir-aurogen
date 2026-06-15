import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from pydantic import BaseModel
from typing import List
from ..database import get_db
from ..models import Event, MenuItem, Transaction, TransactionItem
from .auth import is_admin
from ..templates_config import templates


class EditItem(BaseModel):
    transaction_item_id: int
    qty: int


class EditTransactionRequest(BaseModel):
    items: List[EditItem]

router = APIRouter(prefix="/admin")


def format_rupiah(amount: int) -> str:
    return f"Rp {amount:,}".replace(",", ".")


@router.get("/rekap", response_class=HTMLResponse)
async def rekap_page(
    request: Request,
    event_id: int = None,
    date_filter: str = None,
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=302)

    # Rekap omset per event
    event_summaries = (
        db.query(
            Event.id,
            Event.name,
            Event.start_date,
            Event.end_date,
            Event.is_active,
            func.count(Transaction.id).label("tx_count"),
            func.coalesce(func.sum(Transaction.total), 0).label("total_omset"),
        )
        .outerjoin(Transaction, Transaction.event_id == Event.id)
        .group_by(Event.id)
        .order_by(Event.start_date.desc())
        .all()
    )

    events = db.query(Event).order_by(Event.start_date.desc()).all()

    # Riwayat transaksi
    query = db.query(Transaction).order_by(Transaction.created_at.desc())
    if event_id:
        query = query.filter(Transaction.event_id == event_id)
    if date_filter:
        try:
            filter_date = date.fromisoformat(date_filter)
            query = query.filter(func.date(Transaction.created_at) == filter_date)
        except ValueError:
            pass
    transactions = query.limit(200).all()

    # Rekap harian
    recap_date = None
    recap_data = None
    if date_filter:
        try:
            recap_date = date.fromisoformat(date_filter)
            recap_query = db.query(Transaction).filter(
                func.date(Transaction.created_at) == recap_date
            )
            if event_id:
                recap_query = recap_query.filter(Transaction.event_id == event_id)

            day_txs = recap_query.all()
            omset = sum(t.total for t in day_txs)
            n_tx = len(day_txs)
            avg_tx = omset // n_tx if n_tx > 0 else 0

            item_query = (
                db.query(
                    TransactionItem.item_name,
                    func.sum(TransactionItem.qty).label("total_qty"),
                    func.sum(TransactionItem.subtotal).label("total_revenue"),
                )
                .join(Transaction, TransactionItem.transaction_id == Transaction.id)
                .filter(func.date(Transaction.created_at) == recap_date)
            )
            if event_id:
                item_query = item_query.filter(Transaction.event_id == event_id)
            top_items = (
                item_query.group_by(TransactionItem.item_name)
                .order_by(func.sum(TransactionItem.qty).desc())
                .limit(5)
                .all()
            )

            tunai_txs = [t for t in day_txs if (t.payment_method or "tunai") == "tunai"]
            qris_txs = [t for t in day_txs if (t.payment_method or "tunai") == "qris"]

            recap_data = {
                "omset": omset,
                "n_tx": n_tx,
                "avg_tx": avg_tx,
                "top_items": [
                    {"name": r.item_name, "qty": r.total_qty, "revenue": r.total_revenue}
                    for r in top_items
                ],
                "tunai_count": len(tunai_txs),
                "tunai_total": sum(t.total for t in tunai_txs),
                "qris_count": len(qris_txs),
                "qris_total": sum(t.total for t in qris_txs),
            }
        except ValueError:
            pass

    return templates.TemplateResponse(
        "admin/rekap.html",
        {
            "request": request,
            "event_summaries": event_summaries,
            "events": events,
            "transactions": transactions,
            "selected_event_id": event_id,
            "date_filter": date_filter or "",
            "recap_date": recap_date,
            "recap_data": recap_data,
            "format_rupiah": format_rupiah,
        },
    )


@router.get("/api/transactions/{tx_id}")
async def transaction_detail(tx_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        return JSONResponse({"error": "Transaksi tidak ditemukan."}, status_code=404)
    return JSONResponse({
        "id": tx.id,
        "transaction_number": tx.transaction_number,
        "event_name": tx.event.name if tx.event else "(event dihapus)",
        "created_at": tx.created_at.strftime("%d/%m/%Y %H:%M"),
        "total": tx.total,
        "customer_name": tx.customer_name or "",
        "customer_phone": tx.customer_phone or "",
        "payment_method": tx.payment_method or "tunai",
        "items": [
            {
                "id": i.id,
                "name": i.item_name,
                "qty": i.qty,
                "price": i.item_price,
                "subtotal": i.subtotal,
            }
            for i in tx.items
        ],
    })


@router.delete("/api/transactions/{tx_id}")
async def delete_transaction(tx_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        return JSONResponse({"error": "Transaksi tidak ditemukan."}, status_code=404)

    for item in tx.items:
        if item.menu_item:
            item.menu_item.stock += item.qty

    if tx.struk_path and os.path.exists(tx.struk_path):
        try:
            os.remove(tx.struk_path)
        except Exception:
            pass

    db.delete(tx)
    db.commit()
    return JSONResponse({"success": True})


@router.put("/api/transactions/{tx_id}")
async def update_transaction(
    tx_id: int,
    payload: EditTransactionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        return JSONResponse({"error": "Transaksi tidak ditemukan."}, status_code=404)

    edit_map = {p.transaction_item_id: p.qty for p in payload.items}

    # Pre-validate: after restoring old stock, is new qty available?
    for tx_item in tx.items:
        new_qty = edit_map.get(tx_item.id, tx_item.qty)
        if new_qty > 0 and tx_item.menu_item:
            virtual_stock = tx_item.menu_item.stock + tx_item.qty
            if new_qty > virtual_stock:
                return JSONResponse(
                    {"error": f"Stok {tx_item.item_name} tidak cukup (tersedia: {virtual_stock})."},
                    status_code=400,
                )

    # Restore all old stock
    for tx_item in tx.items:
        if tx_item.menu_item:
            tx_item.menu_item.stock += tx_item.qty

    # Apply new quantities
    items_to_keep = []
    for tx_item in tx.items:
        new_qty = edit_map.get(tx_item.id, tx_item.qty)
        if new_qty <= 0:
            db.delete(tx_item)
        else:
            tx_item.qty = new_qty
            tx_item.subtotal = tx_item.item_price * new_qty
            if tx_item.menu_item:
                tx_item.menu_item.stock -= new_qty
            items_to_keep.append(tx_item)

    if not items_to_keep:
        if tx.struk_path and os.path.exists(tx.struk_path):
            try:
                os.remove(tx.struk_path)
            except Exception:
                pass
        db.delete(tx)
        db.commit()
        return JSONResponse({"success": True, "deleted": True})

    tx.total = sum(i.subtotal for i in items_to_keep)

    if tx.struk_path and os.path.exists(tx.struk_path):
        try:
            os.remove(tx.struk_path)
        except Exception:
            pass
    tx.struk_path = None

    db.commit()
    return JSONResponse({"success": True, "deleted": False, "new_total": tx.total})
