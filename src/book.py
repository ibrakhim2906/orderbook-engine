import uuid
from collections import deque
from decimal import Decimal

from sortedcontainers import SortedDict

from src.models import Order, OrderStatus, Side, Trade


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: SortedDict[Decimal, deque[Order]] = SortedDict()
        self.asks: SortedDict[Decimal, deque[Order]] = SortedDict()
        self.orders: dict[str, Order] = {}
        self._sequence = 0

    def add_order(self, order: Order) -> list[Trade]:
        order.sequence = self._next_sequence()
        return self._match(order)

    def best_bid(self) -> Decimal | None:

        if not self.bids:
            return None

        price, _ = self.bids.peekitem(-1)
        return price  # type: ignore

    def best_ask(self) -> Decimal | None:

        if not self.asks:
            return None

        price, _ = self.asks.peekitem(0)
        return price  # type: ignore

    def _insert_resting(self, order: Order) -> None:

        self.orders[order.order_id] = order

        book_side = self.bids if order.side == Side.BUY else self.asks

        if order.price not in book_side:
            book_side[order.price] = deque()

        book_side[order.price].append(order)

    def _next_sequence(self) -> int:
        self._sequence += 1

        return self._sequence

    def _match(self, incoming: Order) -> list[Trade]:
        trades: list[Trade] = []

        opposite_book = self.asks if incoming.side == Side.BUY else self.bids

        while (
            opposite_book and incoming.remaining_quantity > 0
        ):  # loop while there's ANY liquidity left on the other side
            if opposite_book is self.asks:
                best_price, level_orders = opposite_book.peekitem(0)
            else:
                best_price, level_orders = opposite_book.peekitem(-1)

            if incoming.side == Side.BUY:
                if incoming.price < best_price:
                    break
            elif incoming.side == Side.SELL:
                if incoming.price > best_price:
                    break

            while level_orders and incoming.remaining_quantity > 0:
                resting = level_orders[0]

                if resting.status == OrderStatus.CANCELLED:
                    level_orders.popleft()
                    continue

                trade_qty = min(resting.remaining_quantity, incoming.remaining_quantity)

                resting.remaining_quantity -= trade_qty
                incoming.remaining_quantity -= trade_qty

                if incoming.side == Side.BUY:
                    buy_order_id, sell_order_id = incoming.order_id, resting.order_id
                else:
                    buy_order_id, sell_order_id = resting.order_id, incoming.order_id

                trade = Trade(
                    str(uuid.uuid4()),
                    self.symbol,
                    resting.price,
                    trade_qty,
                    buy_order_id,
                    sell_order_id,
                    self._next_sequence(),
                )

                trades.append(trade)

                if resting.remaining_quantity == 0:
                    level_orders.popleft()
                    resting.status = OrderStatus.FILLED

            if not level_orders:
                del opposite_book[best_price]

        if incoming.remaining_quantity > 0:
            self._insert_resting(incoming)

        return trades
