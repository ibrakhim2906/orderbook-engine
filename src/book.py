from collections import deque
from decimal import Decimal

from sortedcontainers import SortedDict

from src.models import Order, Side


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: SortedDict = SortedDict()  # price -> deque[Order], descending
        self.asks: SortedDict = SortedDict()  # price -> deque[Order], ascending
        self.orders: dict[str, Order] = {}
        self._sequence = 0

    def _next_sequence(self) -> int:
        self._sequence += 1

        return self._sequence

    def _insert_resting(self, order: Order) -> None:

        self.orders[order.order_id] = order

        book_side = self.bids if order.side == Side.BUY else self.asks

        if order.price not in book_side:
            book_side[order.price] = deque()

        book_side[order.price].append(order)

    def best_bid(self) -> Decimal | None:

        if not self.bids:
            return None

        price, _ = self.bids.peekitem(-1)
        return price  # pyright: ignore[reportReturnType]

    def best_ask(self) -> Decimal | None:

        if not self.asks:
            return None

        price, _ = self.asks.peekitem(0)
        return price  # pyright: ignore[reportReturnType]
