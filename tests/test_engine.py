from decimal import Decimal

from src.engine import MatchingEngine
from src.models import OrderStatus, OrderType, Side


def test_multi_symbol_isolation():

    engine = MatchingEngine()

    engine.submit_order(
        owner_id="533",
        symbol="BTCUSD",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    engine.submit_order(
        owner_id="534",
        symbol="ETHUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    assert engine.trade_log == []
    assert engine.get_book("BTCUSD").best_ask() == Decimal("100")
    assert engine.get_book("ETHUSD").best_bid() == Decimal("100")

    _, trades = engine.submit_order(
        owner_id="535",
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    assert len(trades) == 1
    assert len(engine.trade_log) == 1
    assert engine.get_book("ETHUSD").best_bid() == Decimal("100")
    assert engine.get_book("BTCUSD").best_ask() is None


def test_callback_fires_on_submit_order():

    engine = MatchingEngine()
    seen = []
    engine.register_trade_callback(seen.append)

    engine.submit_order(
        owner_id="533",
        symbol="BTCUSD",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    _, trades = engine.submit_order(
        owner_id="534",
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    assert len(trades) == 1
    assert seen == trades
    assert engine.trade_log == trades


def test_callback_fires_on_amend_order():

    engine = MatchingEngine()
    seen = []
    engine.register_trade_callback(seen.append)

    engine.submit_order(
        owner_id="533",
        symbol="BTCUSD",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    buy_order, buy_trades = engine.submit_order(
        owner_id="534",
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("95"),
        quantity=Decimal("10"),
    )

    assert buy_trades == []
    assert seen == []

    success, amend_trades = engine.amend_order(
        symbol="BTCUSD",
        order_id=buy_order.order_id,
        new_price=Decimal("100"),
    )

    assert success
    assert len(amend_trades) == 1
    assert seen == amend_trades
    assert engine.trade_log == amend_trades


def test_cancel_order_routing():

    engine = MatchingEngine()

    order, _ = engine.submit_order(
        owner_id="533",
        symbol="BTCUSD",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    assert engine.cancel_order("BTCUSD", order.order_id)
    assert order.status == OrderStatus.CANCELLED

    assert not engine.cancel_order("BTCUSD", "nonexistent")

    assert not engine.cancel_order("BTCUSD", order.order_id)


def test_amend_order_routing_and_return_shape():

    engine = MatchingEngine()

    order, _ = engine.submit_order(
        owner_id="533",
        symbol="BTCUSD",
        side=Side.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    success, trades = engine.amend_order(
        symbol="BTCUSD",
        order_id=order.order_id,
        new_quantity=Decimal("5"),
    )

    assert success is True
    assert trades == []
    assert order.quantity == Decimal("5")

    engine.submit_order(
        owner_id="534",
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("5"),
    )

    assert order.status == OrderStatus.FILLED

    success, trades = engine.amend_order(
        symbol="BTCUSD",
        order_id=order.order_id,
        new_price=Decimal("200"),
    )

    assert success is False
    assert trades == []


def test_get_book_lazy_creation_and_identity():

    engine = MatchingEngine()

    assert "NEWSYM" not in engine.books

    book_first = engine.get_book("NEWSYM")
    assert book_first is not None
    assert book_first.symbol == "NEWSYM"
    assert book_first.best_bid() is None
    assert book_first.best_ask() is None

    book_second = engine.get_book("NEWSYM")
    assert book_first is book_second
