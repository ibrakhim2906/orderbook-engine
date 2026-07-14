from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class TimeInForce(Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class OrderStatus(Enum):
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    order_id: str
    owner_id: str
    symbol: str
    side: Side
    order_type: OrderType
    time_in_force: TimeInForce
    price: Decimal | None
    quantity: Decimal
    sequence: int
    remaining_quantity: Decimal | None = None
    status: OrderStatus = OrderStatus.OPEN

    def __post_init__(self) -> None:
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity


@dataclass(frozen=True)
class Trade:
    trade_id: str
    symbol: str
    price: Decimal
    quantity: Decimal
    buy_order_id: str
    sell_order_id: str
    sequence: int
