from __future__ import annotations

from datetime import datetime
import sqlite3
from typing import Any

from .db import query_all, query_one


def _parse_iso_date(value: str) -> str:
    # Accept YYYY or YYYY-MM-DD; return ISO range boundaries handled elsewhere
    value = value.strip()
    if len(value) == 4 and value.isdigit():
        return value
    # basic validation
    datetime.fromisoformat(value)  # may raise
    return value


def search_clients(conn: sqlite3.Connection, query: str, limit: int = 5) -> dict[str, Any]:
    query = (query or "").strip()
    limit = max(1, min(int(limit or 5), 20))
    if not query:
        return {"clients": []}

    like = f"%{query}%"
    rows = query_all(
        conn,
        """
        SELECT client_id, name, email
        FROM clients
        WHERE name LIKE ? OR email LIKE ?
        ORDER BY name ASC
        LIMIT ?
        """,
        (like, like, limit),
    )
    return {"clients": [dict(r) for r in rows]}


def get_client(conn: sqlite3.Connection, client_id: int) -> dict[str, Any]:
    row = query_one(
        conn,
        "SELECT client_id, name, email, created_at FROM clients WHERE client_id = ?",
        (int(client_id),),
    )
    if row is None:
        return {"client": None}
    return {"client": dict(row)}


def count_orders_for_client(
    conn: sqlite3.Connection,
    client_id: int,
    status: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    client_id = int(client_id)
    status = (status or "").strip() or None

    where = ["client_id = ?"]
    params: list[Any] = [client_id]

    if status:
        where.append("status = ?")
        params.append(status)

    if from_date:
        fd = _parse_iso_date(from_date)
        if len(fd) == 4:
            where.append("created_at >= ?")
            params.append(f"{fd}-01-01T00:00:00Z")
        else:
            where.append("created_at >= ?")
            params.append(fd if fd.endswith("Z") else fd + "Z")

    if to_date:
        td = _parse_iso_date(to_date)
        if len(td) == 4:
            where.append("created_at < ?")
            params.append(f"{int(td)+1}-01-01T00:00:00Z")
        else:
            where.append("created_at <= ?")
            params.append(td if td.endswith("Z") else td + "Z")

    sql = f"SELECT COUNT(*) AS cnt FROM orders WHERE {' AND '.join(where)}"
    row = query_one(conn, sql, params)
    return {"client_id": client_id, "order_count": int(row["cnt"]) if row else 0}


def sum_orders_for_client(
    conn: sqlite3.Connection,
    client_id: int,
    status: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    client_id = int(client_id)
    status = (status or "").strip() or None

    where = ["client_id = ?"]
    params: list[Any] = [client_id]

    if status:
        where.append("status = ?")
        params.append(status)

    if from_date:
        fd = _parse_iso_date(from_date)
        if len(fd) == 4:
            where.append("created_at >= ?")
            params.append(f"{fd}-01-01T00:00:00Z")
        else:
            where.append("created_at >= ?")
            params.append(fd if fd.endswith("Z") else fd + "Z")

    if to_date:
        td = _parse_iso_date(to_date)
        if len(td) == 4:
            where.append("created_at < ?")
            params.append(f"{int(td)+1}-01-01T00:00:00Z")
        else:
            where.append("created_at <= ?")
            params.append(td if td.endswith("Z") else td + "Z")

    sql = f"SELECT COALESCE(SUM(total_amount), 0) AS total, currency FROM orders WHERE {' AND '.join(where)}"
    row = query_one(conn, sql, params)
    currency = row["currency"] if row and row["currency"] else "PLN"
    total = float(row["total"]) if row else 0.0
    return {"client_id": client_id, "total_amount": total, "currency": currency}


def get_orders_for_client(
    conn: sqlite3.Connection,
    client_id: int,
    status: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    client_id = int(client_id)
    status = (status or "").strip() or None
    limit = max(1, min(int(limit or 5), 50))

    if status:
        rows = query_all(
            conn,
            """
            SELECT order_id, client_id, status, total_amount, currency, created_at
            FROM orders
            WHERE client_id = ? AND status = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (client_id, status, limit),
        )
    else:
        rows = query_all(
            conn,
            """
            SELECT order_id, client_id, status, total_amount, currency, created_at
            FROM orders
            WHERE client_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (client_id, limit),
        )

    return {"client_id": client_id, "orders": [dict(r) for r in rows]}
