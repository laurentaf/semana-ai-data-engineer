"""ShopAgent — Pydantic validation tests for Day 1 models."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from models import Customer, Order, Product, Review


class TestOrder:
    """Tests for Order model."""

    def test_valid_order(self) -> None:
        order = Order(
            order_id=uuid4(),
            customer_id=uuid4(),
            product_id=uuid4(),
            qty=3,
            total=Decimal("149.90"),
            status="delivered",
            payment="pix",
            created_at=datetime.now(),
        )
        assert order.qty == 3
        assert order.status == "delivered"

    def test_qty_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Order(
                order_id=uuid4(),
                customer_id=uuid4(),
                product_id=uuid4(),
                qty=0,
                total=Decimal("50.00"),
                status="shipped",
                payment="credit_card",
                created_at=datetime.now(),
            )

    def test_invalid_payment_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Order(
                order_id=uuid4(),
                customer_id=uuid4(),
                product_id=uuid4(),
                qty=2,
                total=Decimal("99.90"),
                status="processing",
                payment="dinheiro",
                created_at=datetime.now(),
            )

    @pytest.mark.parametrize("invalid_qty", [0, 11, -1, 100])
    def test_invalid_qty_params(self, invalid_qty: int) -> None:
        with pytest.raises(ValidationError):
            Order(
                order_id=uuid4(),
                customer_id=uuid4(),
                product_id=uuid4(),
                qty=invalid_qty,
                total=Decimal("100.00"),
                status="processing",
                payment="boleto",
                created_at=datetime.now(),
            )


class TestReview:
    """Tests for Review model (uses str IDs for JSONL compatibility)."""

    def test_valid_review(self) -> None:
        review = Review(
            review_id="r-001",
            order_id="o-001",
            rating=5,
            comment="Produto excelente, recomendo!",
            sentiment="positive",
        )
        assert review.rating == 5
        assert review.sentiment == "positive"

    def test_rating_above_max_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Review(
                review_id="r-002",
                order_id="o-002",
                rating=6,
                comment="Teste",
                sentiment="positive",
            )

    def test_rating_below_min_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Review(
                review_id="r-003",
                order_id="o-003",
                rating=0,
                comment="Teste",
                sentiment="negative",
            )

    @pytest.mark.parametrize("invalid_rating", [0, 6, -1, 10])
    def test_invalid_rating_params(self, invalid_rating: int) -> None:
        with pytest.raises(ValidationError):
            Review(
                review_id="r-004",
                order_id="o-004",
                rating=invalid_rating,
                comment="Test",
                sentiment="neutral",
            )


class TestCustomer:
    """Tests for Customer model."""

    def test_valid_customer(self) -> None:
        customer = Customer(
            customer_id=uuid4(),
            name="Maria Silva",
            email="maria@example.com",
            city="São Paulo",
            state="SP",
            segment="premium",
        )
        assert customer.segment == "premium"

    def test_invalid_segment_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Customer(
                customer_id=uuid4(),
                name="João",
                email="joao@example.com",
                segment="vip",
            )


class TestProduct:
    """Tests for Product model."""

    def test_valid_product(self) -> None:
        product = Product(
            product_id=uuid4(),
            name="Smartphone XYZ",
            category="electronics",
            price=Decimal("1299.90"),
            brand="TechBrand",
        )
        assert product.price == Decimal("1299.90")

    def test_product_zero_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Product(
                product_id=uuid4(),
                name="Free Item",
                category="electronics",
                price=Decimal("0.00"),
            )

    def test_product_missing_category_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Product(
                product_id=uuid4(),
                name="No Category",
                price=Decimal("99.90"),
            )
