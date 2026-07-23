import json
import sqlite3
from datetime import UTC, datetime
from enum import Enum


class EventType(Enum):
    OrderSubmitted = "order_submitted"
    OrderCancelled = "order_cancelled"
    OrderAmended = "order_amended"


class EventLog:
    def __init__(self, db_path: str):

        self.conn = sqlite3.connect(db_path)
        self._create_table()
        self._sequence = self._load_last_sequence()

    def _create_table(self) -> None:

        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )

        self.conn.commit()

    def _load_last_sequence(self) -> int:

        cursor = self.conn.execute("SELECT MAX(sequence) FROM events")

        row = cursor.fetchone()
        max_sequence = row[0]

        return max_sequence if max_sequence is not None else 0

    def append(self, event_type: str, payload: dict):

        self._sequence += 1

        json_string = json.dumps(payload)

        created_at = datetime.now(UTC).isoformat()

        self.conn.execute(
            "INSERT INTO events (sequence, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (self._sequence, event_type, json_string, created_at),
        )

        self.conn.commit()

        return self._sequence

    def read_all(self) -> list[tuple[int, str, dict]]:

        events = []

        cursor = self.conn.execute(
            "SELECT sequence, event_type, payload FROM events ORDER BY sequence"
        )

        rows = cursor.fetchall()

        for row in rows:
            payload = json.loads(row[2])

            events.append((row[0], row[1], payload))

        return events

    def close(self) -> None:

        self.conn.close()
