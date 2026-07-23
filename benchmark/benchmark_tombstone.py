import random
import statistics
import timeit
from decimal import Decimal

from benchmark.benchmark_submit import SEED
from src.engine import MatchingEngine
from src.models import OrderStatus, OrderType, Side

CANCEL_PROBABILITY = 0.33


def create_cancel_heavy_plan(
    n: int, seed: int, cancel_probability: float, lowest_price: int, highest_price: int
) -> list[tuple]:

    rng = random.Random(seed)
    plan = []

    submitted_count = 0

    for i in range(n):
        if submitted_count > 0 and rng.random() < cancel_probability:
            index_to_cancel = rng.randint(0, submitted_count - 1)
            plan.append(("cancel", index_to_cancel))

        else:
            order_info = dict(
                owner_id=f"TR_{i % 60}",
                symbol="BTCUSD",
                side=rng.choice([Side.BUY, Side.SELL]),
                order_type=OrderType.LIMIT,
                price=Decimal(rng.randint(lowest_price, highest_price)),
                quantity=Decimal(rng.randint(1, 20)),
            )

            plan.append(("submit", order_info))

            submitted_count += 1

    return plan


def run_plan(engine: MatchingEngine, plan: list[tuple]) -> tuple[int, int]:

    submitted_ids: list[str] = []
    submit_count = 0
    cancel_count = 0

    for action, payload in plan:
        if action == "submit":
            order, _ = engine.submit_order(**payload)

            submitted_ids.append(order.order_id)

            submit_count += 1

        elif action == "cancel":
            order_id = submitted_ids[payload]

            if engine.cancel_order("BTCUSD", order_id):
                cancel_count += 1

    return submit_count, cancel_count


def make_trial_fn(plan):

    def trial():

        engine = MatchingEngine()
        run_plan(engine, plan)

    return trial


def count_tombstones_in_book(engine: MatchingEngine, symbol: str) -> tuple[int, int]:

    book = engine.get_book(symbol)

    live = 0
    tombstones = 0

    for side in (book.bids, book.asks):
        for price in side:
            for order in side[price]:
                if order.status == OrderStatus.CANCELLED:
                    tombstones += 1

                else:
                    live += 1

    return live, tombstones


def benchmark(
    name: str, n: int, lowest_price: int, highest_price: int, trials: int = 5
):

    plan = create_cancel_heavy_plan(
        n, SEED, CANCEL_PROBABILITY, lowest_price, highest_price
    )

    trial_fn = make_trial_fn(plan)

    timer = timeit.Timer(stmt=trial_fn)
    results = timer.repeat(repeat=trials, number=1)

    time_median = statistics.median(results)
    throughput = n / time_median

    diag_engine = MatchingEngine()
    submit_count, cancel_count = run_plan(diag_engine, plan)
    live, tombstones = count_tombstones_in_book(diag_engine, "BTCUSD")

    print(f"\n--- {name} ---")
    print(f"Orders: {n}, trials: {trials}")
    print(f"All trial times: {[f'{t:.4f}s' for t in results]}")
    print(f"Median time: {time_median:.4f}s")
    print(f"Throughput: {throughput:,.0f} orders/sec")
    print(
        f"Final book state: {live} live orders, {tombstones} tombstoned orders still in deques"
    )
    print(
        f"Tombstone ratio: {tombstones / (live + tombstones) * 100:.1f}% of resting deque entries are garbage"
    )


if __name__ == "__main__":
    benchmark(
        f"Cancel-heavy ({CANCEL_PROBABILITY * 100}% cancel rate)",
        n=10_000,
        lowest_price=1,
        highest_price=1000,
    )
