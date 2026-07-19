from decimal import Decimal

from src.book import OrderBook
from src.models import Side
from tests.test_models import make_order


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
