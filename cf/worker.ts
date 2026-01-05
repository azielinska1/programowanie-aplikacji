export interface Env {
  ASSETS: Fetcher;
  GEMINI_MODEL: string;
  // GEMINI_API_KEY ustaw jako secret: `wrangler secret put GEMINI_API_KEY`
  GEMINI_API_KEY?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Minimalny placeholder: UI działa na Cloudflare, ale backend FastAPI nie.
    if (url.pathname === "/api/chat" && request.method === "POST") {
      const body = {
        answer:
          "API /api/chat nie jest jeszcze przeniesione na Cloudflare Workers. " +
          "FastAPI (Python) nie działa natywnie na Workers. " +
          "Masz 2 opcje: (1) UI na Cloudflare Pages/Workers + backend na Render/Fly/Azure, " +
          "albo (2) port backendu do Worker (TypeScript) + D1 zamiast SQLite."
      };
      return new Response(JSON.stringify(body), {
        headers: { "content-type": "application/json; charset=utf-8" }
      });
    }

    // Statyczne pliki (index.html, styles.css, app.js)
    return env.ASSETS.fetch(request);
  }
};
