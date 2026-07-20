from decimal import Decimal

from src.models import Order, OrderType, Side, TimeInForce


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
