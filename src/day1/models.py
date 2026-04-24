"""ShopAgent - Pydantic models for the 4 core entities.

Week 1: INGERIR (Data Generation)
- Customer, Product, Order (Postgres/Ledger)
- Review (JSONL/RAG Memory)
"""
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Customer(BaseModel):
    """E-commerce customer entity."""

    customer_id: UUID
    name: str
    email: str
    city: Optional[str] = None
    state: Optional[str] = None
    segment: Literal["premium", "standard", "basic"]


class Product(BaseModel):
    """E-commerce product entity."""

    product_id: UUID
    name: str
    category: str
    price: Decimal = Field(ge=0)
    brand: Optional[str] = None


class Order(BaseModel):
    """E-commerce order (fact table)."""

    order_id: UUID
    customer_id: UUID
    product_id: UUID
    qty: int = Field(ge=1, le=10)
    total: Decimal = Field(ge=0)
    status: Literal["delivered", "shipped", "processing", "cancelled"]
    payment: Literal["pix", "credit_card", "boleto"]
    created_at: datetime


class Review(BaseModel):
    """Customer review for RAG/semantic search."""

    review_id: str
    order_id: str
    rating: int = Field(ge=1, le=5)
    comment: str
    sentiment: Literal["positive", "neutral", "negative"]


__all__ = ["Customer", "Product", "Order", "Review"]
