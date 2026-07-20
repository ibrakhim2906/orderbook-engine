from decimal import Decimal

from src.book import OrderBook
from src.models import OrderStatus, Side
from tests.conftest import make_order


def test_canceling_order_basics():

    book = OrderBook("BTCUSD")
    sell = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("100")
    )

    book.add_order(sell)

    assert book.cancel_order(sell.order_id)
    assert sell.status == OrderStatus.CANCELLED

    nonexistent_id = "50"

    assert not book.cancel_order(nonexistent_id)

    sell = make_order(
        order_id="2", side=Side.SELL, price=Decimal("100"), quantity=Decimal("100")
    )
    sell.status = OrderStatus.FILLED

    book.add_order(sell)

    assert not book.cancel_order(sell.order_id)
