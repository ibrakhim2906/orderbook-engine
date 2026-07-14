from decimal import Decimal

from src.book import OrderBook
from src.models import Side
from tests.test_models import make_order


def test_empty_book_no_best_bid_or_ask():
    book = OrderBook(symbol="BTCUSD")

    assert book.best_ask() is None
    assert book.best_bid() is None


def test_best_bid_correct():
    book = OrderBook(symbol="BTCUSD")

    for i in range(1, 4):
        book._insert_resting(
            make_order(order_id=str(i), side=Side.BUY, price=Decimal(str(i + 100)))
        )

    assert book.best_bid() == Decimal("103")


def test_best_ask_correct():

    book = OrderBook(symbol="BTCUSD")

    for i in range(1, 4):
        book._insert_resting(
            make_order(order_id=str(i), side=Side.SELL, price=Decimal(str(i + 100)))
        )

    assert book.best_ask() == Decimal("101")


def test_same_price_fifo_preserved():

    book = OrderBook(symbol="BTCUSD")

    first = make_order(order_id="1", side=Side.BUY, price=Decimal("100"))
    second = make_order(order_id="1", side=Side.BUY, price=Decimal("100"))

    book._insert_resting(first)
    book._insert_resting(second)

    level = book.bids[Decimal("100")]

    assert level[0] is first
    assert level[1] is second


def test_inserted_order_is_registered_in_lookup_index():

    book = OrderBook(symbol="BTCUSD")

    order = make_order(order_id="42")
    book._insert_resting(order)

    assert book.orders["42"] is order
