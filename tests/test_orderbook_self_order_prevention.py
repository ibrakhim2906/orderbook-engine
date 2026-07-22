from decimal import Decimal

from src.book import OrderBook
from src.models import OrderStatus, Side
from tests.conftest import make_order


def test_self_trade_detected_on_match():

    book = OrderBook("BTCUSD")
    sell = make_order(
        order_id="1",
        owner_id="533",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("50"),
    )
    buy = make_order(
        order_id="2",
        owner_id="533",
        side=Side.BUY,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    book.add_order(sell)

    trades = book.add_order(buy)

    assert not trades
    assert sell.remaining_quantity == sell.quantity


def test_self_trade_partial_fill_then_marks_status_correctly():

    book = OrderBook("BTCUSD")

    sell_other = make_order(
        order_id="1",
        owner_id="534",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("3"),
    )

    sell_self = make_order(
        order_id="2",
        owner_id="533",
        side=Side.SELL,
        price=Decimal("101"),
        quantity=Decimal("10"),
    )

    buy_self_trade = make_order(
        order_id="3",
        owner_id="533",
        side=Side.BUY,
        price=Decimal("101"),
        quantity=Decimal("10"),
    )

    book.add_order(sell_other)
    book.add_order(sell_self)
    trades = book.add_order(buy_self_trade)

    assert len(trades) == 1
    assert trades[0].quantity == Decimal("3")
    assert buy_self_trade.status == OrderStatus.PARTIALLY_FILLED
    assert buy_self_trade.remaining_quantity == Decimal("7")
