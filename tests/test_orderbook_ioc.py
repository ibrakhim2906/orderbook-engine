from decimal import Decimal

from src.book import OrderBook
from src.models import Side, TimeInForce
from tests.conftest import make_order


def test_ico_timeinforce_order_remaining_amount_do_not_rest():

    book = OrderBook("BTCUSD")
    sell_order = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("10")
    )
    buy_order_ioc = make_order(
        order_id="2",
        side=Side.BUY,
        price=Decimal("100"),
        quantity=Decimal("15"),
        time_in_force=TimeInForce.IOC,
    )

    book.add_order(sell_order)
    book.add_order(buy_order_ioc)

    assert buy_order_ioc.remaining_quantity > 0
    assert buy_order_ioc.order_id not in book.orders
