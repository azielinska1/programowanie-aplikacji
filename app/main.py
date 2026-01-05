from __future__ import annotations

import sqlite3
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import connect, init_db
from .seed import seed_if_empty
from .schemas import ChatRequest, ChatResponse
from . import tools as tool_mod
from .gemini import chat_with_tools, GeminiError


app = FastAPI(title="lab8 - klienci i zamówienia")


def _get_conn() -> sqlite3.Connection:
    settings = get_settings()
    conn = connect(settings.sqlite_path)
    init_db(conn)
    seed_if_empty(conn)
    return conn


@app.on_event("startup")
def _startup() -> None:
    conn = _get_conn()
    conn.close()


@app.get("/")
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    settings = get_settings()
    conn = _get_conn()

    try:
        tool_impl = {
            "search_clients": lambda query, limit=5: tool_mod.search_clients(conn, query=query, limit=limit),
            "get_client": lambda client_id: tool_mod.get_client(conn, client_id=client_id),
            "count_orders_for_client": lambda client_id, status=None, from_date=None, to_date=None: tool_mod.count_orders_for_client(
                conn,
                client_id=client_id,
                status=status,
                from_date=from_date,
                to_date=to_date,
            ),
            "sum_orders_for_client": lambda client_id, status=None, from_date=None, to_date=None: tool_mod.sum_orders_for_client(
                conn,
                client_id=client_id,
                status=status,
                from_date=from_date,
                to_date=to_date,
            ),
            "get_orders_for_client": lambda client_id, status=None, limit=5: tool_mod.get_orders_for_client(
                conn,
                client_id=client_id,
                status=status,
                limit=limit,
            ),
        }

        answer, trace = await chat_with_tools(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            user_message=req.message,
            tool_impl=tool_impl,
        )

        return ChatResponse(
            answer=answer,
            tool_trace=trace if settings.debug_tool_trace else None,
        )

    except GeminiError as e:
        return ChatResponse(answer=f"Błąd Gemini: {e}")

    finally:
        conn.close()
