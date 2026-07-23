import os
import tempfile
from decimal import Decimal

from src.engine import MatchingEngine
from src.eventlog import EventLog
from src.models import OrderType, Side


def test_append_and_read_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        log = EventLog(db_path)

        seq1 = log.append("order_submitted", {"order_id": "1", "quantity": "10"})
        seq2 = log.append("order_cancelled", {"order_id": "1"})

        assert seq1 == 1
        assert seq2 == 2

        events = log.read_all()
        assert len(events) == 2
        assert events[0] == (1, "order_submitted", {"order_id": "1", "quantity": "10"})
        assert events[1] == (2, "order_cancelled", {"order_id": "1"})

        log.close()


def test_sequence_resumes_after_reopening_existing_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")

        log1 = EventLog(db_path)
        log1.append("order_submitted", {"order_id": "1"})
        log1.append("order_submitted", {"order_id": "2"})
        log1.close()

        log2 = EventLog(db_path)
        seq3 = log2.append("order_submitted", {"order_id": "3"})

        assert seq3 == 3
        log2.close()


def test_replay_reconstructs_engine_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "replay.db")

        log = EventLog(db_path)
        original_engine = MatchingEngine(event_log=log)

        original_engine.submit_order(
            owner_id="533",
            symbol="BTCUSD",
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("100"),
            quantity=Decimal("10"),
        )
        resting, _ = original_engine.submit_order(
            owner_id="534",
            symbol="BTCUSD",
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("90"),
            quantity=Decimal("5"),
        )
        original_engine.amend_order(
            symbol="BTCUSD",
            order_id=resting.order_id,
            new_price=Decimal("100"),
        )
        cancel_me, _ = original_engine.submit_order(
            owner_id="535",
            symbol="BTCUSD",
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("105"),
            quantity=Decimal("3"),
        )
        original_engine.cancel_order("BTCUSD", cancel_me.order_id)

        log.close()

        replay_log = EventLog(db_path)
        replayed_engine = MatchingEngine(event_log=None)
        replayed_engine.replay_from(replay_log)
        replay_log.close()

        original_book = original_engine.get_book("BTCUSD")
        replayed_book = replayed_engine.get_book("BTCUSD")

        assert set(replayed_book.orders.keys()) == set(original_book.orders.keys())

        for order_id, original_order in original_book.orders.items():
            replayed_order = replayed_book.orders[order_id]
            assert replayed_order.status == original_order.status
            assert (
                replayed_order.remaining_quantity == original_order.remaining_quantity
            )
            assert replayed_order.price == original_order.price
            assert replayed_order.quantity == original_order.quantity

        assert len(replayed_engine.trade_log) == len(original_engine.trade_log)
        for original_trade, replayed_trade in zip(
            original_engine.trade_log, replayed_engine.trade_log
        ):
            assert replayed_trade.price == original_trade.price
            assert replayed_trade.quantity == original_trade.quantity
            assert replayed_trade.buy_order_id == original_trade.buy_order_id
            assert replayed_trade.sell_order_id == original_trade.sell_order_id
