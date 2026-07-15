from decimal import Decimal

from src.book import OrderBook
from src.models import Side
from tests.test_models import make_order


def test_exact_match_full_fill():
    book = OrderBook("BTCUSD")
    sell = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("100")
    )
    buy = make_order(
        order_id="2", side=Side.BUY, price=Decimal("100"), quantity=Decimal("100")
    )

    book.add_order(sell)
    trades = book.add_order(buy)

    assert len(trades) == 1
    assert trades[0].quantity == Decimal("100")
    assert trades[0].price == Decimal("100")
    assert buy.remaining_quantity == 0
    assert sell.remaining_quantity == 0
    assert book.best_bid() is None
    assert book.best_ask() is None


def test_partial_fill_incoming_smaller():

    book = OrderBook(symbol="BTCUSD")
    sell = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("10")
    )
    buy = make_order(
        order_id="2", side=Side.BUY, price=Decimal("100"), quantity=Decimal("5")
    )

    book.add_order(sell)
    trades = book.add_order(buy)

    assert len(trades) == 1
    assert trades[0].quantity == Decimal("5")
    assert buy.remaining_quantity == Decimal("0")
    assert sell.remaining_quantity == Decimal("5")
    assert book.best_ask() == Decimal("100")


def test_partial_fill_incoming_sweeps_two_levels():

    book = OrderBook("BTCUSD")
    sell_level1 = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("10")
    )
    sell_level2 = make_order(
        order_id="2", side=Side.SELL, price=Decimal("101"), quantity=Decimal("5")
    )

    buy = make_order(
        order_id="3", side=Side.BUY, price=Decimal("101"), quantity=Decimal("15")
    )

    book.add_order(sell_level1)
    book.add_order(sell_level2)

    trades = book.add_order(buy)

    assert len(trades) == 2
    assert trades[0].price == Decimal("100")
    assert trades[0].quantity == Decimal("10")
    assert trades[1].price == Decimal("101")
    assert trades[1].quantity == Decimal("5")
    assert sell_level1.remaining_quantity == 0
    assert sell_level2.remaining_quantity == 0
    assert buy.remaining_quantity == 0


def test_fifo_tie_break_earlier_order_filled_first():

    book = OrderBook("BTCUSD")
    sell_a = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("10")
    )
    sell_b = make_order(
        order_id="2", side=Side.SELL, price=Decimal("100"), quantity=Decimal("10")
    )
    buy = make_order(
        order_id="3", side=Side.BUY, price=Decimal("100"), quantity=Decimal("10")
    )

    book.add_order(sell_a)
    book.add_order(sell_b)
    trades = book.add_order(buy)

    assert len(trades) == 1
    assert trades[0].sell_order_id == "1"
    assert sell_a.remaining_quantity == Decimal("0")
    assert sell_b.remaining_quantity == Decimal("10")


def test_cancelled_order_is_skipped():

    book = OrderBook("BTCUSD")
    sell_a = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("100")
    )
    sell_b = make_order(
        order_id="2", side=Side.SELL, price=Decimal("100"), quantity=Decimal("100")
    )

    buy = make_order(
        order_id="3", side=Side.BUY, price=Decimal("100"), quantity=Decimal("100")
    )

    book.add_order(sell_a)
    book.cancel_order(sell_a.order_id)
    book.add_order(sell_b)

    trades = book.add_order(buy)

    assert len(trades) == 1
    assert trades[0].sell_order_id == "2"
    assert sell_b.remaining_quantity == Decimal("0")


def test_no_match_when_prices_dont_cross():

    book = OrderBook(symbol="BTCUSD")
    sell = make_order(
        order_id="1", side=Side.SELL, price=Decimal("100"), quantity=Decimal("5")
    )
    buy = make_order(
        order_id="2", side=Side.BUY, price=Decimal("95"), quantity=Decimal("5")
    )

    book.add_order(sell)
    trades = book.add_order(buy)

    assert len(trades) == 0
    assert book.best_bid() == Decimal("95")
    assert book.best_ask() == Decimal("100")
