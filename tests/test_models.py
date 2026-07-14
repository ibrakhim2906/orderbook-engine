from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from src.models import Order, OrderStatus, OrderType, Side, TimeInForce, Trade


def make_order(**overrides):
    defaults = dict(
        order_id="1",
        owner_id="trader_1",
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        price=Decimal("100"),
        quantity=Decimal("50"),
        sequence=0,
    )
    defaults.update(overrides)
    return Order(**defaults)


def test_order_defaults_remaining_quantity_to_quantity():
    order = make_order(quantity=Decimal("50"))
    assert order.remaining_quantity == Decimal("50")


def test_order_defaults_status_to_open():
    order = make_order()
    assert order.status == OrderStatus.OPEN


def test_order_explicit_remaining_quantity_is_respected():
    order = make_order(quantity=Decimal("50"), remaining_quantity=Decimal("20"))
    assert order.remaining_quantity == Decimal("20")


def test_order_explicit_status_is_respected():
    order = make_order(status=OrderStatus.CANCELLED)
    assert order.status == OrderStatus.CANCELLED


def test_order_market_order_allows_none_price():
    order = make_order(order_type=OrderType.MARKET, price=None)
    assert order.price is None


def test_trade_fields_set_correctly():
    trade = Trade(
        trade_id="t1",
        symbol="BTCUSD",
        price=Decimal("100"),
        quantity=Decimal("200"),
        buy_order_id="b1",
        sell_order_id="s1",
        sequence=0,
    )
    assert trade.price == Decimal("100")
    assert trade.quantity == Decimal("200")
    assert trade.buy_order_id == "b1"
    assert trade.sell_order_id == "s1"


def test_trade_is_frozen():
    trade = Trade(
        trade_id="t1",
        symbol="BTCUSD",
        price=Decimal("100"),
        quantity=Decimal("200"),
        buy_order_id="b1",
        sell_order_id="s1",
        sequence=0,
    )
    with pytest.raises(FrozenInstanceError):
        trade.price = Decimal("999")
