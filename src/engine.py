import uuid
from decimal import Decimal
from typing import Callable

from src.book import OrderBook
from src.eventlog import EventLog, EventType
from src.models import Order, OrderType, Side, TimeInForce, Trade


class MatchingEngine:
    def __init__(self, event_log: EventLog | None = None):

        self.books: dict[str, OrderBook] = {}
        self.trade_log: list[Trade] = []
        self._on_trade_callbacks: list[Callable[[Trade], None]] = []
        self.event_log = event_log

    def submit_order(
        self,
        owner_id: str,
        symbol: str,
        side: Side,
        order_type: OrderType,
        quantity: Decimal,
        price: Decimal | None = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        order_id: str | None = None,
    ) -> tuple[Order, list[Trade]]:

        if order_type == OrderType.LIMIT and price is None:
            raise ValueError("LIMIT orders require a price")
        if order_type == OrderType.MARKET and price is not None:
            raise ValueError("MARKET orders must not have a price")

        order = Order(
            order_id=order_id if order_id is not None else str(uuid.uuid4()),
            owner_id=owner_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            price=price,
            quantity=quantity,
            sequence=0,
        )

        if self.event_log is not None:
            payload = {
                "order_id": order.order_id,
                "owner_id": owner_id,
                "symbol": symbol,
                "side": side.value,
                "order_type": order_type.value,
                "time_in_force": time_in_force.value,
                "price": str(price) if price is not None else None,
                "quantity": str(quantity),
            }

            self.event_log.append(EventType.OrderSubmitted.value, payload)

        book = self.get_book(symbol)
        trades = book.add_order(order)

        self.trade_log.extend(trades)
        for trade in trades:
            for callback in self._on_trade_callbacks:
                callback(trade)

        return order, trades

    def cancel_order(self, symbol: str, order_id: str) -> bool:

        book = self.get_book(symbol)

        result = book.cancel_order(order_id)

        if result and self.event_log is not None:
            payload = {"symbol": symbol, "order_id": order_id}

            self.event_log.append(EventType.OrderCancelled.value, payload)

        return result

    def amend_order(
        self,
        symbol: str,
        order_id: str,
        new_price: Decimal | None = None,
        new_quantity: Decimal | None = None,
        new_order_id: str | None = None,
    ) -> tuple[bool, list[Trade]]:

        book = self.get_book(symbol)
        success, trades, resulting_order_id = book.amend_order(
            order_id, new_price, new_quantity, new_order_id
        )

        if success and self.event_log is not None:
            payload = {
                "symbol": symbol,
                "order_id": order_id,
                "new_price": str(new_price) if new_price is not None else None,
                "new_quantity": str(new_quantity) if new_quantity is not None else None,
                "resulting_order_id": resulting_order_id,
            }

            self.event_log.append(EventType.OrderAmended.value, payload)

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

    def replay_from(self, event_log: EventLog) -> None:

        for _sequence, event_type, payload in event_log.read_all():
            if event_type == EventType.OrderSubmitted.value:
                self.submit_order(
                    owner_id=payload["owner_id"],
                    symbol=payload["symbol"],
                    side=Side(payload["side"]),
                    order_type=OrderType(payload["order_type"]),
                    quantity=Decimal(payload["quantity"]),
                    price=(
                        Decimal(payload["price"])
                        if payload["price"] is not None
                        else None
                    ),
                    time_in_force=TimeInForce(payload["time_in_force"]),
                    order_id=payload["order_id"],
                )

            elif event_type == EventType.OrderCancelled.value:
                self.cancel_order(payload["symbol"], payload["order_id"])

            elif event_type == EventType.OrderAmended.value:
                new_price = (
                    Decimal(payload["new_price"])
                    if payload["new_price"] is not None
                    else None
                )

                new_quantity = (
                    Decimal(payload["new_quantity"])
                    if payload["new_quantity"] is not None
                    else None
                )

                self.amend_order(
                    payload["symbol"],
                    payload["order_id"],
                    new_price,
                    new_quantity,
                    new_order_id=payload.get("resulting_order_id"),
                )
