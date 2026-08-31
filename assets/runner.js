/* 统一的代码运行入口。三种跑法：浏览器内置 Python、本地 Python、服务器 Python。
   后两种是同一套 HTTP 接口，服务器通过 SSH 端口转发映射到本机地址。 */
(function () {
  const DEFAULT_URL = "http://127.0.0.1:8760";

  class BrowserEngine {
    constructor(opts) {
      this.opts = opts || {};
      this.worker = null;
      this.booting = null;
      this.seq = 0;
      this.pending = new Map();
      this.version = "";
    }
    _spawn() {
      const w = new Worker(this.opts.workerUrl || "../assets/pyworker.js");
      w.onmessage = (ev) => {
        const p = this.pending.get(ev.data.id);
        if (p) { this.pending.delete(ev.data.id); p(ev.data); }
      };
      w.onerror = (e) => {
        for (const [, p] of this.pending) p({ ok: false, output: "运行环境加载失败：" + e.message });
        this.pending.clear();
      };
      return w;
    }
    _send(msg) {
      const id = ++this.seq;
      return new Promise((res) => { this.pending.set(id, res); this.worker.postMessage({ ...msg, id }); });
    }
    async boot(onProgress) {
      if (this.booting) return this.booting;
      this.booting = (async () => {
        if (onProgress) onProgress("正在下载 Python 运行环境");
        this.worker = this._spawn();
        let modules = {};
        if (this.opts.modulesUrl) modules = await (await fetch(this.opts.modulesUrl)).json();
        const r = await this._send({ type: "init", packages: this.opts.packages || [], modules });
        if (!r || !r.version) throw new Error((r && r.output) || "运行环境没起来");
        this.version = r.version;
        if (onProgress) onProgress("");
        return r;
      })().catch((err) => { this.booting = null; throw err; });   // 失败了要能重试
      return this.booting;
    }
    async _reboot() {
      if (this.worker) this.worker.terminate();
      this.booting = null;
      this.pending.clear();
      await this.boot();
    }
    async run(code, stdin, timeoutMs) {
      await this.boot();
      const limit = timeoutMs || this.opts.timeout || 60000;
      let timer;
      const timeout = new Promise((res) => {
        timer = setTimeout(() => res({ ok: false, output: "[超时] 运行超过 " + Math.round(limit / 1000) + " 秒被终止。写了 while 循环的话，检查一下条件是不是永远为真。", timedOut: true }), limit);
      });
      const r = await Promise.race([this._send({ type: "run", code, stdin: stdin || "" }), timeout]);
      clearTimeout(timer);
      if (r.timedOut) await this._reboot();
      return r;
    }
    label() { return this.version ? "浏览器 Python " + this.version : "浏览器 Python"; }
  }

  class BackendEngine {
    constructor(url) { this.url = (url || DEFAULT_URL).replace(/\/+$/, ""); this.version = ""; }
    async boot() {
      const r = await fetch(this.url + "/api/env", { mode: "cors" });
      const j = await r.json();
      this.version = j.python || "";
      this.host = j.host || "";
      return j;
    }
    async run(code, stdin) {
      const r = await fetch(this.url + "/api/run", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, stdin: stdin || "" }),
      });
      const j = await r.json();
      return { ok: j.ok !== false, output: j.output || "", figs: j.figs || [] };
    }
    async check(code, id) {
      const r = await fetch(this.url + "/api/check", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, id }),
      });
      return await r.json();
    }
    label() {
      const where = this.host ? this.host : this.url.replace(/^https?:\/\//, "");
      return this.version ? where + " · Python " + this.version : where;
    }
  }

  const Runner = {
    DEFAULT_URL,
    opts: {},
    engine: null,
    checks: null,
    configure(opts) { this.opts = opts || {}; },
    get mode() { return localStorage.getItem("runMode") || "browser"; },
    set mode(v) { localStorage.setItem("runMode", v); this.engine = null; },
    get url() { return localStorage.getItem("runUrl") || DEFAULT_URL; },
    set url(v) { localStorage.setItem("runUrl", v || DEFAULT_URL); this.engine = null; },
    get() {
      if (!this.engine) {
        this.engine = this.mode === "backend" ? new BackendEngine(this.url) : new BrowserEngine(this.opts);
      }
      return this.engine;
    },
    async boot(onProgress) { return this.get().boot(onProgress); },
    async run(code, stdin, timeoutMs) { return this.get().run(code, stdin, timeoutMs); },
    async loadChecks() {
      if (!this.checks && this.opts.checksUrl) this.checks = await (await fetch(this.opts.checksUrl)).json();
      return this.checks;
    },
    async check(code, id) {
      if (this.mode === "backend") return this.get().check(code, id);
      const checks = await this.loadChecks();
      const rule = checks && checks[String(id)];
      if (!rule) return { ok: null, msg: "这道题暂时没有自动判定，自己对照预期结果看看。" };
      const r = await this.run(code + "\n\n" + (rule.append || ""));
      const out = r.output || "";
      const items = rule.items.map(([desc, needle]) => ({ desc, pass: out.includes(needle) }));
      const passed = items.filter((it) => it.pass).length;
      const ok = passed === items.length;
      let msg;
      if (ok) msg = "全部通过，" + items.length + " 项检查都对了。";
      else if (passed === 0 && !r.ok) msg = "代码没能跑通，先看下面的报错。";
      else msg = "通过 " + passed + " 项，还差 " + (items.length - passed) + " 项。";
      return { ok, msg, items, output: out };
    },
    label() { return this.get().label(); },
  };

  window.Runner = Runner;
})();
