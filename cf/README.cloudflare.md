# Cloudflare (Wrangler) — Opcja A

UI jest hostowane na Cloudflare (Workers + assets), a endpoint `/api/chat` jest **proxy** do zewnętrznego backendu FastAPI.

## Wymagania
- Działający backend FastAPI wystawiony publicznie po HTTPS (np. Render/Fly.io/Azure App Service).

## Konfiguracja
Ustaw `BACKEND_URL` w [wrangler.toml](wrangler.toml) albo w Cloudflare dashboard jako zmienną środowiskową.
Przykład:
- `BACKEND_URL = "https://twoj-backend.example.com"`

## Dev
- `wrangler dev`

## Deploy
- `wrangler deploy`

## Dlaczego tak?
Cloudflare Workers uruchamiają kod JS/TS/WASM. Python/FastAPI nie działa natywnie na Workers, więc proxy pozwala zachować UI na Cloudflare bez problemów CORS.
