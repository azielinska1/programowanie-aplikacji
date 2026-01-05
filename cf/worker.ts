export interface Env {
  ASSETS: Fetcher;
  GEMINI_MODEL: string;
  // GEMINI_API_KEY ustaw jako secret: `wrangler secret put GEMINI_API_KEY`
  GEMINI_API_KEY?: string;
  // Publiczny URL backendu FastAPI, np. https://twoj-backend.example.com
  BACKEND_URL: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Opcja A: UI na Cloudflare, backend FastAPI gdzie indziej.
    // Proxy utrzymuje ten sam origin dla przeglądarki (brak problemów CORS).
    if (url.pathname === "/api/chat") {
      if (!env.BACKEND_URL) {
        return new Response(
          JSON.stringify({
            answer:
              "Brak konfiguracji BACKEND_URL w Workerze. Ustaw zmienną w wrangler.toml albo Cloudflare dashboard."
          }),
          { headers: { "content-type": "application/json; charset=utf-8" }, status: 500 }
        );
      }

      const backendBase = new URL(env.BACKEND_URL);
      const target = new URL(url.pathname + url.search, backendBase);

      const proxyReq = new Request(target.toString(), request);
      // Cloudflare nie pozwala nadpisać Host przez headers.set w Request clone, ale to nie jest potrzebne.
      const resp = await fetch(proxyReq);

      // Przepuść odpowiedź 1:1 (JSON) - UI oczekuje { answer, tool_trace? }
      return resp;
    }

    // Statyczne pliki (index.html, styles.css, app.js)
    return env.ASSETS.fetch(request);
  }
};
