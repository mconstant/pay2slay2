export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = env.ORIGIN_HOST;
    if (!origin) {
      return new Response("ORIGIN_HOST not configured", { status: 502 });
    }
    const target = new URL(url.pathname + url.search, "https://" + origin);
    const proxyReq = new Request(target, {
      method: request.method,
      headers: request.headers,
      body: request.body,
      redirect: "manual",
    });
    proxyReq.headers.set("Host", origin);
    const resp = await fetch(proxyReq);
    const proxyResp = new Response(resp.body, resp);
    proxyResp.headers.set("X-Origin", origin);
    return proxyResp;
  },
};
