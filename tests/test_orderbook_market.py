from decimal import Decimal

from src.book import OrderBook
from src.models import OrderType, Side
from tests.test_models import make_order


def test_market_buy_sweeps_multiple_levels():

    book = OrderBook("BTCUSD")
    sell_a = make_order(
        order_id="1",
        owner_id="533",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("100"),
    )
    sell_b = make_order(
        order_id="2",
        owner_id="534",
        side=Side.SELL,
        price=Decimal("100"),
        quantity=Decimal("100"),
    )

    market_buy = make_order(
        order_id="3",
        owner_id="535",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        price=None,
        quantity=Decimal("200"),
    )

    book.add_order(sell_a)
    book.add_order(sell_b)

    trades = book.add_order(market_buy)

    assert len(trades) == 2
    assert trades[0].price == Decimal("100")
    assert trades[1].price == Decimal("100")
    assert market_buy.remaining_quantity == Decimal("0")


def test_market_with_no_liquidity_drops_order():

    book = OrderBook("BTCUSD")
    market_buy = make_order(
        order_id="3",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        price=None,
        quantity=Decimal("200"),
    )

    trades = book.add_order(market_buy)

    assert len(trades) == 0
    assert market_buy.order_id not in book.orders
    assert book.best_bid() is None
