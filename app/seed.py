from __future__ import annotations

from datetime import datetime
import random
import sqlite3

from .db import query_one, execute


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def seed_if_empty(conn: sqlite3.Connection) -> None:
    clients = [
        ("ACME Sp. z o.o.", "contact@acme.example"),
        ("Beta S.A.", "office@beta.example"),
        ("Gamma Consulting", "hello@gamma.example"),
        ("Delta Logistics", "contact@delta.example"),
        ("Epsilon Retail", "office@epsilon.example"),
        ("Zeta Media", "hello@zeta.example"),
        ("Eta Software", "contact@eta.example"),
        ("Theta Foods", "office@theta.example"),
        ("Iota Finance", "hello@iota.example"),
        ("Kappa Energy", "contact@kappa.example"),
        ("Lambda Design", "office@lambda.example"),
        ("Mu Motors", "hello@mu.example"),
        ("Nu Health", "contact@nu.example"),
        ("Xi Travel", "office@xi.example"),
        ("Omicron Education", "hello@omicron.example"),
        ("Pi Construction", "contact@pi.example"),
        ("Rho Security", "office@rho.example"),
        ("Sigma Pharma", "hello@sigma.example"),
        ("Tau Furniture", "contact@tau.example"),
        ("Upsilon Telecom", "office@upsilon.example"),
    ]

    client_ids: list[int] = []
    for name, email in clients:
        # Try to re-use existing rows to avoid duplicates when re-running.
        row = query_one(conn, "SELECT client_id FROM clients WHERE email = ?", (email,))
        if row is None:
            row = query_one(conn, "SELECT client_id FROM clients WHERE name = ?", (name,))

        if row is None:
            client_id = execute(
                conn,
                "INSERT INTO clients(name, email, created_at) VALUES (?, ?, ?)",
                (name, email, _now_iso()),
            )
        else:
            client_id = int(row["client_id"])

        client_ids.append(client_id)

    statuses = ["new", "paid", "shipped", "cancelled"]
    for client_id in client_ids:
        existing_orders_row = query_one(conn, "SELECT COUNT(*) AS cnt FROM orders WHERE client_id = ?", (client_id,))
        existing_orders = int(existing_orders_row["cnt"]) if existing_orders_row else 0
        # Ensure more than one order per person.
        missing_to_two = max(0, 2 - existing_orders)
        extra = random.randint(0, 4)
        to_create = missing_to_two + extra
        for _ in range(to_create):
            status = random.choice(statuses)
            amount = round(random.uniform(50, 1200), 2)
            created_at = _random_date_2025_iso()
            execute(
                conn,
                "INSERT INTO orders(client_id, status, total_amount, currency, created_at) VALUES (?, ?, ?, ?, ?)",
                (client_id, status, amount, "PLN", created_at),
            )


def _random_date_2025_iso() -> str:
    # deterministic enough for demo; keeps dates in 2025
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)
    seconds = int((end - start).total_seconds())
    dt = start + (end - start) * random.random()
    return dt.replace(microsecond=0).isoformat() + "Z"
