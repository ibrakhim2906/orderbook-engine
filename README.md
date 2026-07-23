# Order Book Matching Engine

A FIFO (price-time priority) order book matching engine built from scratch in Python

The engine offers limit and market orders, GTC/IOC/FOK time-in-force, order cancelation, amendment with correct rules, self-trade prevention, and durable event logging with full state replay ability. Careful testing include 39 unit/integration tests plus property-based test that helped to indicate four significant semantical bugs during development.

# What it can do

- **price-time priority matching** -- orders at the best price filled first, while among same price levels, whoever order arrived first is being filled first.
- **order-types** -- limit and market order types are supported.
- **time-in-force** -- GTC (rests until filled or cancelled), IOC (fills what it can immediately, cancels the rest), FOK (filled completely or not at all) time-in-force types can be set up.
- **self-trade-prevention** -- an order can't match againt another order from the same owner
- **event logging** -- every accepted submit/cancel/amend orders logged to sqlite, and the whole book state can be rebuilt by replaying the log


