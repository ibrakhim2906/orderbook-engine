import random
import statistics
import timeit
from decimal import Decimal

from src.engine import MatchingEngine
from src.models import OrderType, Side

SEED = 67


def create_random_order_batch(
    n: int, seed: int, lowest_price: int, highest_price: int
) -> list[dict]:

    rng = random.Random(seed)
    orders = []

    for i in range(n):
        orders.append(
            dict(
                owner_id=f"TR_{i % 60}",
                symbol="BTCUSD",
                side=rng.choice([Side.BUY, Side.SELL]),
                order_type=OrderType.LIMIT,
                price=Decimal(rng.randint(lowest_price, highest_price)),
                quantity=Decimal(rng.randint(1, 20)),
            )
        )

    return orders


def load_batch(engine: MatchingEngine, orders: list[dict]) -> None:

    for order in orders:
        engine.submit_order(**order)


def make_trial_fn(orders: list[dict]):

    def trial():
        engine = MatchingEngine()
        load_batch(engine, orders)

    return trial


def benchmark(
    name: str, n: int, lowest_price: int, highest_price: int, trials: int = 5
) -> None:

    orders = create_random_order_batch(n, SEED, lowest_price, highest_price)
    trial_fn = make_trial_fn(orders)

    timer = timeit.Timer(stmt=trial_fn)
    results = timer.repeat(repeat=trials, number=1)

    time_median = statistics.median(results)
    throughput = n / time_median

    print(f"\n--- {name} ---")
    print(f"Orders: {n}, trials: {trials}")
    print(f"Seed given: {SEED}")
    print(f"All trial times: {[f'{t:.4f}s' for t in results]}")
    print(f"Median time: {time_median:.4f}s")
    print(f"Throughput: {throughput:,.0f} orders/sec")


# def report_final_book_size(name: str, orders: list[dict]) -> None:

#     engine = MatchingEngine()
#     load_batch(engine, orders)

#     book = engine.get_book("BTCUSD")

#     resting_count = sum(
#         1
#         for o in book.orders.values()
#         if o.status
#         not in (OrderStatus.CANCELLED, OrderStatus.FILLED, OrderStatus.REJECTED)
#     )

#     print(f"  Final resting orders in book ({name}): {resting_count}")


if __name__ == "__main__":
    benchmark(
        "Resting-only (wide spread)", n=10_000, lowest_price=1, highest_price=1000
    )

    benchmark(
        "Heavy crossing (narrow spread)", n=10_000, lowest_price=99, highest_price=101
    )
