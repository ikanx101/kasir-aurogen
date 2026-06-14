from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False)

    menu_items = relationship("MenuItem", back_populates="event", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="event", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    event = relationship("Event", back_populates="menu_items")
    transaction_items = relationship("TransactionItem", back_populates="menu_item")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    transaction_number = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    total = Column(Integer, nullable=False)
    struk_path = Column(String, nullable=True)

    event = relationship("Event", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)
    item_name = Column(String, nullable=False)
    item_price = Column(Integer, nullable=False)
    qty = Column(Integer, nullable=False)
    subtotal = Column(Integer, nullable=False)

    transaction = relationship("Transaction", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="transaction_items")
