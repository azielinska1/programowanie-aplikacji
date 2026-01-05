export interface Env {
  ASSETS?: Fetcher;
  GEMINI_MODEL: string;
  // GEMINI_API_KEY ustaw jako secret: `wrangler secret put GEMINI_API_KEY`
  GEMINI_API_KEY?: string;
  // Publiczny URL backendu FastAPI, np. https://twoj-backend.example.com
  BACKEND_URL: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
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

        let backendBase: URL;
        try {
          backendBase = new URL(env.BACKEND_URL);
        } catch {
          return new Response(
            JSON.stringify({
              answer:
                `BACKEND_URL nie jest poprawnym URL: ${String(env.BACKEND_URL)}`
            }),
            { headers: { "content-type": "application/json; charset=utf-8" }, status: 500 }
          );
        }

        const target = new URL(url.pathname + url.search, backendBase);
        const proxyReq = new Request(target.toString(), request);
        const resp = await fetch(proxyReq);
        return resp;
      }

      if (!env.ASSETS) {
        return new Response(
          "Brak bindingu ASSETS. Ten Worker musi być wdrożony z assets (wrangler.toml: assets = { directory = \"./app\" }).",
          { status: 500, headers: { "content-type": "text/plain; charset=utf-8" } }
        );
      }

      // Statyczne pliki (UI jest w /static/*, bo FastAPI tak serwuje lokalnie)
      // Przy assets = { directory = "./app" } pliki są dostępne jako /static/...
      if (url.pathname === "/") {
        const rewritten = new URL(request.url);
        rewritten.pathname = "/static/index.html";
        return env.ASSETS.fetch(new Request(rewritten.toString(), request));
      }

      return env.ASSETS.fetch(request);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return new Response(`Worker error: ${msg}`,
        { status: 500, headers: { "content-type": "text/plain; charset=utf-8" } }
      );
    }
  }
};
