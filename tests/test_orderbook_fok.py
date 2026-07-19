from decimal import Decimal

from src.book import OrderBook
from src.models import OrderStatus, Side, TimeInForce
from tests.test_models import make_order


def test_fok_rejected_not_enough_liquidity():

    book = OrderBook("BTCUSD")

    sell = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("5")
    )

    book.add_order(sell)

    buy_fok = make_order(
        order_id="2",
        side=Side.BUY,
        price=Decimal("100"),
        time_in_force=TimeInForce.FOK,
        quantity=Decimal("10"),
    )

    trades = book.add_order(buy_fok)

    assert not trades
    assert buy_fok.status == OrderStatus.REJECTED
    assert sell.remaining_quantity == Decimal("5")
    assert book.best_ask() == Decimal("100")


def test_fok_fills_completely_two_levels():

    book = OrderBook("BTCUSD")
    sell_a = make_order(
        order_id="1",
        owner_id="533",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("5"),
    )
    sell_b = make_order(
        order_id="2",
        owner_id="534",
        side=Side.SELL,
        price=Decimal("101"),
        quantity=Decimal("5"),
    )

    buy_fok = make_order(
        order_id="3",
        owner_id="535",
        side=Side.BUY,
        price=Decimal("101"),
        quantity=Decimal("10"),
    )

    book.add_order(sell_a)
    book.add_order(sell_b)

    trades = book.add_order(buy_fok)

    assert len(trades) == 2
    assert buy_fok.remaining_quantity == Decimal("0")
    assert book.best_ask() is None
