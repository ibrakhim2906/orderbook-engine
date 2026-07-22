import itertools
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from src.book import OrderBook
from src.models import Side
from tests.conftest import assert_invariant, make_order

order_side_st = st.sampled_from([Side.BUY, Side.SELL])
price_st = st.decimals(min_value=Decimal("90"), max_value=Decimal("110"), places=0)
quantity_st = st.decimals(min_value=Decimal("1"), max_value=Decimal("20"), places=0)
owner_st = st.sampled_from(["t1", "t2", "t3"])
order_id_counter = itertools.count(1)


@st.composite
def order_st(draw):
    return make_order(
        order_id=str(next(order_id_counter)),
        owner_id=draw(owner_st),
        side=draw(order_side_st),
        price=draw(price_st),
        quantity=draw(quantity_st),
    )


@given(orders=st.lists(order_st(), min_size=1, max_size=50))
@settings(max_examples=1000)
def test_invariant_holds_under_coming_orders(orders):

    book = OrderBook("BTCUSD")
    all_trades = []
    all_submitted_orders = []

    for order in orders:
        all_submitted_orders.append(order)
        trades = book.add_order(order)
        all_trades.extend(trades)

    assert_invariant(book, all_trades, all_submitted_orders)
