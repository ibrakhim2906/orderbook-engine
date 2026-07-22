from decimal import Decimal

from src.book import OrderBook
from src.models import Side
from tests.conftest import make_order


def test_amending_price_loses_priority():

    book = OrderBook("BTCUSD")

    sell_a = make_order(
        order_id="1",
        owner_id="533",
        side=Side.SELL,
        price=Decimal("99"),
        quantity=Decimal("10"),
    )

    sell_b = make_order(
        order_id="2",
        owner_id="534",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    book.add_order(sell_a)
    book.add_order(sell_b)

    book.amend_order(order_id="1", new_price=Decimal("100"))

    buy = make_order(
        order_id="3",
        owner_id="535",
        side=Side.BUY,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )
    trades = book.add_order(buy)

    assert len(trades) == 1
    assert trades[0].sell_order_id == "2"


def test_only_amending_quantity_saved_priority():

    book = OrderBook("BTCUSD")

    sell_a = make_order(
        order_id="1",
        owner_id="533",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    sell_b = make_order(
        order_id="2",
        owner_id="534",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    book.add_order(sell_a)
    book.add_order(sell_b)

    book.amend_order(order_id="1", new_quantity=Decimal("5"))

    price = Decimal("100")  # Both orders A and B are at the same price
    assert book.asks[price][0] is sell_a


def test_cannot_amend_cancelled_or_filled_order():

    book = OrderBook("BTCUSD")

    sell = make_order(
        order_id="1",
        owner_id="533",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )
    buy = make_order(
        order_id="2",
        owner_id="534",
        side=Side.BUY,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    book.add_order(sell)
    book.add_order(buy)

    success, trades = book.amend_order(order_id="1", new_price=Decimal("200"))

    assert not success
    assert trades == []
