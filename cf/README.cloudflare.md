# Cloudflare (Wrangler)

Ten katalog dodaje minimalny Worker, żeby Wrangler miał **entry-point** i mógł wdrożyć statyczne UI z `app/static`.

## Dlaczego nie działa FastAPI na Workers?
Cloudflare Workers uruchamiają kod JS/TS/WASM. Python/FastAPI nie działa tam bez portowania.

## Dev
- `wrangler dev`

## Deploy
- `wrangler deploy`

## Sekrety
Jeśli później przeniesiesz /api/chat na Worker, ustaw sekret:
- `wrangler secret put GEMINI_API_KEY`

## Uwaga
W tej wersji `/api/chat` zwraca komunikat informacyjny (placeholder).
