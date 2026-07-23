# Order Book Matching Engine

A FIFO (price-time priority) order book matching engine built from scratch in Python

The engine offers limit and market orders, GTC/IOC/FOK time-in-force, order cancelation, amendment with correct rules, self-trade prevention, and durable event logging with full state replay ability. Careful testing include 39 unit/integration tests plus property-based test that helped to indicate four significant semantical bugs during development.

## What it can do

- **price-time priority matching** -- orders at the best price filled first, while among same price levels, whoever order arrived first is being filled first.
- **order-types** -- limit and market order types are supported.
- **time-in-force** -- GTC (rests until filled or cancelled), IOC (fills what it can immediately, cancels the rest), FOK (filled completely or not at all) time-in-force types can be set up.
- **self-trade-prevention** -- an order can't match againt another order from the same owner
- **event logging** -- every accepted submit/cancel/amend orders logged to sqlite, and the whole book state can be rebuilt by replaying the log

## Design Decisions

**Sorted Dict + deque** give O(1) FIFO within a price level. 'SortedDict' gives O(log n) best-price access and level insert/remove.

**lazy cancelation (tombstoning)**. 'deque' do not allow to cheaply remove orders from the middle, so cancel is being done just by flipping the status of order, allowing to be skipped when encountering with order that has 'CANCELLED' status, therefore - O(1) time complexity achieved. Tradeoff is that cancelled orders are being left in deque, which make them memory inefficient.

**amend** is done in following manner:
- new_price or bigger quantity loses priority (new order is added to the deque)
- smaller quantity keeps order priority (in-place edit)

**self-trade prevention**. after encountering first self-trade, matching stops, you get what you can before encounterment.

**sqlite, raw sql, no orm**. fully synchronous logging accepted because of simplicity and engine being fully synchronous (two sql statements are being done, one generic table)

## Testing

39 tests: exact/partial fills, multi-level sweeps, FIFO tie-breaks, market sweeps, IOC/FOK, self-trade prevention, amend priority rules, tombstoning, multi-symbol isolation, trade callbacks, full event-log replay.

on top of that, a hypothesis property-based test generates random order/cancel sequences and checks one invariant after each run:

```
2 * (total quantity traded) + (total quantity still outstanding) == (total quantity submitted)
```

event logging cost real throughput - commit-per-write can be quite expenstive

| scenario | no event log | with event log | slowdown |
|---|---|---|---|
| resting-only | 194k orders/sec | 5.2k orders/sec | ~37x |
| heavy crossing | 201k orders/sec | 5.3k orders/sec | ~38x |
| cancel-heavy | 282k actions/sec | 7.3k actions/sec | ~38x |



## How to run it

```bash
uv sync
uv run pytest -v                        # full test suite
uv run pytest --cov=src                 # with coverage
uv run mypy src/                        # type check
uv run ruff check .                     # lint
uv run python -m benchmark.benchmark_submit      # throughput benchmark
uv run python -m benchmark.benchmark_tombstone   # cancel-heavy / tombstone benchmark
```

## Future additions / Limitations

- **no api** - scope choice, focus was on correctness and performance
- **no compaction for tombstoned order** - can be fixed, because in a long run substantial performance slow down can be expected
- **single-file logging** - can be expanded for close to production systems


