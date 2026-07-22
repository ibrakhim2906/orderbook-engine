import uuid
from decimal import Decimal
from typing import Callable

from src.book import OrderBook
from src.models import Order, OrderType, Side, TimeInForce, Trade


class MatchingEngine:
    def __init__(self):

        self.books: dict[str, OrderBook] = {}
        self.trade_log: list[Trade] = []
        self._on_trade_callbacks: list[Callable[[Trade], None]] = []

    def submit_order(
        self,
        owner_id: str,
        symbol: str,
        side: Side,
        order_type: OrderType,
        quantity: Decimal,
        price: Decimal | None = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
    ) -> tuple[Order, list[Trade]]:
        if order_type == OrderType.LIMIT and price is None:
            raise ValueError("LIMIT orders require a price")
        if order_type == OrderType.MARKET and price is not None:
            raise ValueError("MARKET orders must not have a price")

        order = Order(
            order_id=str(uuid.uuid4()),
            owner_id=owner_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            price=price,
            quantity=quantity,
            sequence=0,  # placeholder, overwritten inside OrderBook.add_order
        )

        book = self.get_book(symbol)
        trades = book.add_order(order)

        self.trade_log.extend(trades)
        for trade in trades:
            for callback in self._on_trade_callbacks:
                callback(trade)

        return order, trades

    def cancel_order(self, symbol: str, order_id: str) -> bool:

        book = self.get_book(symbol)

        return book.cancel_order(order_id)

    def amend_order(
        self, symbol: str, order_id: str, new_price=None, new_quantity=None
    ) -> tuple[bool, list[Trade]]:

        book = self.get_book(symbol)
        success, trades = book.amend_order(order_id, new_price, new_quantity)

        self.trade_log.extend(trades)
        for trade in trades:
            for callback in self._on_trade_callbacks:
                callback(trade)

        return success, trades

    def get_book(self, symbol: str) -> OrderBook:

        if symbol not in self.books:
            self.books[symbol] = OrderBook(symbol)

        return self.books[symbol]

    def register_trade_callback(self, fn: Callable[[Trade], None]) -> None:

        self._on_trade_callbacks.append(fn)
