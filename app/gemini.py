from __future__ import annotations

import json
from typing import Any, Callable

import httpx


# Some model names are only available (or supported for generateContent)
# in certain API versions. We'll try both.
GEMINI_BASES = (
    # Prefer v1beta first because tool/function calling is supported there.
    "https://generativelanguage.googleapis.com/v1beta",
    "https://generativelanguage.googleapis.com/v1",
)


class GeminiError(RuntimeError):
    pass


def _normalize_model_name(model: str) -> str:
    m = (model or "").strip()
    if m.startswith("models/"):
        m = m[len("models/") :].strip()
    return m


def _function_declarations() -> list[dict[str, Any]]:
    # Gemini function calling schema: tools: [{ functionDeclarations: [...] }]
    return [
        {
            "name": "search_clients",
            "description": "Wyszukaj klientów po nazwie lub email. Zwraca listę dopasowań (max limit).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Fraza wyszukiwania"},
                    "limit": {"type": "integer", "description": "Maksymalna liczba wyników (1-20)", "default": 5},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_client",
            "description": "Pobierz klienta po client_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer"},
                },
                "required": ["client_id"],
            },
        },
        {
            "name": "count_orders_for_client",
            "description": "Policz zamówienia klienta (opcjonalnie filtr: status, zakres dat).",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "from_date": {"type": "string", "description": "YYYY lub YYYY-MM-DD"},
                    "to_date": {"type": "string", "description": "YYYY lub YYYY-MM-DD"},
                },
                "required": ["client_id"],
            },
        },
        {
            "name": "sum_orders_for_client",
            "description": "Suma wartości zamówień klienta (opcjonalnie filtr: status, zakres dat).",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "from_date": {"type": "string", "description": "YYYY lub YYYY-MM-DD"},
                    "to_date": {"type": "string", "description": "YYYY lub YYYY-MM-DD"},
                },
                "required": ["client_id"],
            },
        },
        {
            "name": "get_orders_for_client",
            "description": "Zwróć listę ostatnich zamówień klienta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "limit": {"type": "integer", "default": 5, "description": "1-50"},
                },
                "required": ["client_id"],
            },
        },
    ]


SYSTEM_PROMPT_PL = (
    "Jesteś asystentem do bazy klientów i zamówień. "
    "Nie zgaduj danych z bazy. Jeśli potrzebujesz danych, użyj narzędzi. "
    "Gdy wyszukujesz klienta i jest kilka dopasowań, poproś użytkownika o doprecyzowanie. "
    "Odpowiadaj krótko i konkretnie po polsku. "
    "Jeśli nie znasz odpowiedzi, przyznaj się do tego zamiast wymyślać. "

)


async def chat_with_tools(
    *,
    api_key: str,
    model: str,
    user_message: str,
    tool_impl: dict[str, Callable[..., dict[str, Any]]],
    max_steps: int = 8,
) -> tuple[str, list[dict[str, Any]]]:
    if not api_key:
        raise GeminiError("Brak GEMINI_API_KEY w .env")

    normalized_model = _normalize_model_name(model)
    if not normalized_model:
        raise GeminiError("Brak GEMINI_MODEL w .env")

    contents: list[dict[str, Any]] = [
        {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT_PL}\n\nUżytkownik: {user_message}"}]}
    ]

    tool_trace: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(max_steps):
            payload_with_tools = {
                "contents": contents,
                "tools": [{"functionDeclarations": _function_declarations()}],
            }
            payload_no_tools = {
                "contents": contents,
            }

            resp: httpx.Response | None = None
            last_error_text: str | None = None
            for base in GEMINI_BASES:
                url = f"{base}/models/{normalized_model}:generateContent"

                # First try with tools (function calling).
                resp = await client.post(url, params={"key": api_key}, json=payload_with_tools)

                if resp.status_code == 404:
                    # Try the other API version before failing.
                    last_error_text = resp.text
                    continue

                # Some API versions/keys don't support the 'tools' field.
                if resp.status_code == 400 and 'Unknown name "tools"' in (resp.text or ""):
                    resp = await client.post(url, params={"key": api_key}, json=payload_no_tools)

                break

            if resp is None:
                raise GeminiError("Nie udało się wywołać Gemini API")

            if resp.status_code >= 400:
                # If we tried both bases and still got 404, provide a clearer hint.
                if resp.status_code == 404 and last_error_text:
                    raise GeminiError(
                        "Model nie został znaleziony albo nie obsługuje generateContent. "
                        "Sprawdź GEMINI_MODEL (np. gemini-2.5-flash lub gemini-2.0-flash) "
                        f"— szczegóły: {last_error_text}"
                    )
                raise GeminiError(f"Gemini HTTP {resp.status_code}: {resp.text}")

            data = resp.json()
            candidates = data.get("candidates") or []
            if not candidates:
                raise GeminiError("Brak candidates w odpowiedzi Gemini")

            parts = ((candidates[0].get("content") or {}).get("parts")) or []

            function_calls = [p.get("functionCall") for p in parts if p.get("functionCall")]
            if function_calls:
                # Execute all function calls in order, append functionResponse parts.
                response_parts: list[dict[str, Any]] = []
                for call in function_calls:
                    name = call.get("name")
                    args = call.get("args") or {}
                    if name not in tool_impl:
                        raise GeminiError(f"Nieznane narzędzie: {name}")

                    try:
                        result = tool_impl[name](**args)
                    except Exception as e:  # noqa: BLE001
                        result = {"error": str(e)}

                    tool_trace.append({"tool": name, "args": args, "result": result})
                    response_parts.append(
                        {
                            "functionResponse": {
                                "name": name,
                                "response": {"result": result},
                            }
                        }
                    )

                contents.append({"role": "model", "parts": parts})
                contents.append({"role": "user", "parts": response_parts})
                continue

            # No tool calls: expect text answer.
            text_chunks = [p.get("text") for p in parts if p.get("text")]
            answer = "\n".join([t for t in text_chunks if t]).strip()
            if not answer:
                # fall back to stringifying full content
                answer = json.dumps(candidates[0].get("content"), ensure_ascii=False)
            return answer, tool_trace

    raise GeminiError("Przekroczono limit kroków narzędzi")
