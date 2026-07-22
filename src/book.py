import uuid
from collections import deque
from decimal import Decimal

from sortedcontainers import SortedDict

from src.models import Order, OrderStatus, OrderType, Side, TimeInForce, Trade


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: SortedDict[Decimal, deque[Order]] = SortedDict()
        self.asks: SortedDict[Decimal, deque[Order]] = SortedDict()
        self.orders: dict[str, Order] = {}
        self._sequence = 0

    def add_order(self, order: Order) -> list[Trade]:
        order.sequence = self._next_sequence()

        if order.time_in_force == TimeInForce.FOK:
            if not self._can_fully_fill(order):
                order.status = OrderStatus.REJECTED
                return []

        return self._match(order)

    def amend_order(
        self, order_id: str, new_price=None, new_quantity=None
    ) -> tuple[bool, list[Trade]]:

        order = self.orders.get(order_id)

        if not order:
            return False, []

        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
            return False, []

        is_price_changed = new_price is not None and new_price != order.price
        is_quantity_increased = (
            new_quantity is not None and new_quantity > order.quantity
        )

        if (
            not is_price_changed
            and not is_quantity_increased
            and new_quantity is not None
        ):
            already_filled = order.quantity - order.remaining_quantity

            if already_filled > new_quantity:
                return False, []

            order.quantity = new_quantity
            order.remaining_quantity = new_quantity - already_filled

            return True, []

        order.status = OrderStatus.CANCELLED

        new_order = Order(
            order_id=str(uuid.uuid4()),
            owner_id=order.owner_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            time_in_force=order.time_in_force,
            price=new_price if new_price is not None else order.price,
            quantity=new_quantity if new_quantity is not None else order.quantity,
            sequence=0,
        )

        trades = self.add_order(new_order)  # correct here — self is the OrderBook

        return True, trades

    def cancel_order(self, order_id: str) -> bool:

        if order_id not in self.orders:
            return False

        if self.orders[order_id].status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
            return False

        self.orders[order_id].status = OrderStatus.CANCELLED

        return True

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

    def depth(self, levels: int) -> dict:

        return {
            "bids": self._side_depth(self.bids, levels, reverse=True),
            "asks": self._side_depth(self.asks, levels, reverse=False),
        }

    def _side_depth(
        self, book_side: SortedDict, levels: int, reverse: bool
    ) -> list[tuple]:

        result = []

        prices = reversed(book_side.keys()) if reverse else book_side.keys()

        for price in prices:
            if len(result) >= levels:
                break

            total = Decimal("0")

            for order in book_side[price]:
                if order.status != OrderStatus.CANCELLED:
                    total += order.remaining_quantity

            result.append((price, total))

        return result

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

            if incoming.order_type != OrderType.MARKET:
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

                if resting.owner_id == incoming.owner_id:
                    if incoming.remaining_quantity == incoming.quantity:
                        incoming.status = OrderStatus.REJECTED
                    elif incoming.remaining_quantity < incoming.quantity:
                        incoming.status = OrderStatus.PARTIALLY_FILLED

                    return trades

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

        if incoming.remaining_quantity == 0:
            incoming.status = OrderStatus.FILLED
        elif incoming.remaining_quantity < incoming.quantity:
            incoming.status = OrderStatus.PARTIALLY_FILLED

        if (
            incoming.remaining_quantity > 0
            and incoming.order_type != OrderType.MARKET
            and incoming.time_in_force != TimeInForce.IOC
        ):
            self._insert_resting(incoming)

        return trades

    def _can_fully_fill(self, incoming: Order) -> bool:

        opposite_book = self.bids if incoming.side == Side.SELL else self.asks

        collected_quantity = Decimal("0")

        prices = (
            opposite_book.keys()
            if opposite_book is self.asks
            else reversed(opposite_book)
        )

        for price in prices:
            if incoming.side == Side.BUY:
                if incoming.price < price:
                    break
            elif incoming.side == Side.SELL:
                if incoming.price > price:
                    break

            for order in opposite_book[price]:
                if order.status == OrderStatus.CANCELLED:
                    continue

                collected_quantity += order.remaining_quantity

                if collected_quantity >= incoming.quantity:
                    return True

        return False
