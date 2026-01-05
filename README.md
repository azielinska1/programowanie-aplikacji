# lab8 — Klienci i zamówienia + Gemini (tools)

Minimalna aplikacja: web UI → FastAPI ("MCP"/orchestrator + tools) → SQLite (klienci + zamówienia) oraz Gemini jako LLM z function-calling.

## Wymagania
- Python 3.10+

## Start
1. Skopiuj `.env.example` do `.env` i ustaw `GEMINI_API_KEY`.
2. Zainstaluj zależności:
   - `pip install -r requirements.txt`
3. Uruchom serwer:
   - `python -m uvicorn app.main:app --reload`
4. Otwórz w przeglądarce:
   - `http://127.0.0.1:8000/`

## Przykładowe pytania
- "Ile zamówień ma klient ACME?"
- "Pokaż ostatnie 5 zamówień klienta Beta" 
- "Jaka jest suma zamówień klienta ACME w 2025?"

## Uwagi
- Dane startowe seedują się automatycznie przy pierwszym uruchomieniu (jeśli baza jest pusta).
- Narzędzia mają limity wyników i zwracają tylko potrzebne pola.
