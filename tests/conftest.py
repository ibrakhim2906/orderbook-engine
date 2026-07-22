from decimal import Decimal

from src.book import OrderBook
from src.models import Order, OrderStatus, OrderType, Side, TimeInForce, Trade


def make_order(**overrides):
    defaults = dict(
        order_id="1",
        owner_id="trader_1",
        symbol="BTCUSD",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        price=Decimal("100"),
        quantity=Decimal("50"),
        sequence=0,
    )
    defaults.update(overrides)
    return Order(**defaults)


# def total_remaining_quantity(book: OrderBook) -> Decimal:

#     total = Decimal("0")

#     for price in book.bids:
#         for order in book.bids[price]:
#             if order.status != OrderStatus.CANCELLED:
#                 total += order.remaining_quantity

#     for price in book.asks:
#         for order in book.asks[price]:
#             if order.status != OrderStatus.CANCELLED:
#                 total += order.remaining_quantity

#     return total


def assert_invariant(
    book: OrderBook, all_trades: list[Trade], all_submitted_orders: list[Order]
):

    total_submitted = sum(
        o.quantity for o in all_submitted_orders if o.status != OrderStatus.REJECTED
    )

    total_traded = sum(t.quantity for t in all_trades)

    total_remaining = sum(
        o.remaining_quantity
        for o in all_submitted_orders
        if o.status != OrderStatus.REJECTED
    )

    assert 2 * total_traded + total_remaining == total_submitted
