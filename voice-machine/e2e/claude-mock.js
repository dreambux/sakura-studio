/* Atrapa środowiska artefaktu (window.claude) zgodna z typami 0.2.96 (claude.d.ts, mcp.d.ts, tts.d.ts, downloads.d.ts).
   Konfiguracja z adresu: ?cfg={"noHost":true,"noTts":true,"noClaude":true}. Zapisy testowe w window.__saves, window.__ttsCalls. */
(() => {
  const cfg = (() => { try { return JSON.parse(new URLSearchParams(location.search).get('cfg') || '{}'); } catch { return {}; } })();
  window.__saves = [];
  window.__ttsCalls = [];
  window.__hostCalls = [];
  if (cfg.noClaude) return;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const mcp = {
    async listTools() {
      if (cfg.noHost) return { servers: [] };
      const j = await (await fetch('/tools')).json();
      return { servers: [{ server: 'host:sakura-voice', authStatus: 'connected', tools: j.tools }] };
    },
    async callTool(server, tool, input, options) {
      window.__hostCalls.push({ server, tool });
      if (cfg.noHost || server !== 'host:sakura-voice') throw { code: 'server_not_connected', message: 'no host', server };
      if (cfg.denyCalls) throw { code: 'not_in_manifest', message: 'denied', server };
      let res;
      try {
        res = await fetch('/call', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ tool, input }), signal: options && options.signal });
      } catch (e) {
        throw { code: e && e.name === 'AbortError' ? 'cancelled' : 'upstream_error', message: String(e) };
      }
      const j = await res.json();
      if (j.isError) throw { code: 'tool_error', message: (j.content && j.content[0] && j.content[0].text) || 'tool error', result: j };
      return { content: j.content, structuredContent: j.structuredContent, payload: j.structuredContent };
    },
    async server() { throw { code: 'bad_request', message: 'unused' }; },
    async describeTool() { throw { code: 'bad_request', message: 'no schema' }; },
    async invalidate() {},
    watchTool() { return () => {}; },
  };

  let ttsState = 'idle';
  const handlers = [];
  const emit = (state, reason) => handlers.forEach((h) => h(reason ? { state, reason } : { state }));
  const tts = {
    async voices() { return ['buttery', 'airy', 'glassy', 'rounded']; },
    async languages() { return ['en', 'pl']; },
    async speak(what, options) {
      window.__ttsCalls.push({ what, options });
      ttsState = 'speaking'; emit('speaking');
      await sleep(cfg.ttsMs || 200);
      ttsState = 'idle'; emit('idle', 'completed');
      return { playedMs: 200 };
    },
    async add() { return { playedMs: 0 }; },
    async stop() { ttsState = 'idle'; emit('idle', 'stopped'); },
    async pause() {}, async resume() {}, async setRate() {},
    active() { return ttsState !== 'idle'; },
    onState(h) { handlers.push(h); return () => { const i = handlers.indexOf(h); if (i >= 0) handlers.splice(i, 1); }; },
    onLine() { return () => {}; }, onPosition() { return () => {}; },
  };

  const downloads = {
    async save(request) {
      const buf = request.data instanceof Blob ? new Uint8Array(await request.data.arrayBuffer()) : request.data;
      window.__saves.push({ filename: request.filename, bytes: Array.from(buf) });
      return { status: 'saved' };
    },
  };

  const caps = { mcp, downloads };
  if (!cfg.noTts) caps.tts = tts;
  window.claude = { use: async (name) => caps[name] || null };
})();
