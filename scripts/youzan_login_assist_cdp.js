#!/usr/bin/env node

const fs = require("fs");
const http = require("http");
const path = require("path");

const DEFAULT_URL = "https://www.youzan.com/v4/statcenter/custompeek/index";

function parseArgs(argv) {
  const args = {
    cdp: "http://127.0.0.1:9222",
    mode: "status",
    url: DEFAULT_URL,
    output: path.join(process.cwd(), "youzan-login.png"),
    code: "",
    selector: "",
    waitSeconds: 300,
    pollSeconds: 5,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i];
    const next = argv[i + 1];
    if (key === "--cdp") args.cdp = next, i += 1;
    else if (key === "--mode") args.mode = next, i += 1;
    else if (key === "--url") args.url = next, i += 1;
    else if (key === "--output") args.output = next, i += 1;
    else if (key === "--code") args.code = next, i += 1;
    else if (key === "--selector") args.selector = next, i += 1;
    else if (key === "--wait-seconds") args.waitSeconds = Number(next), i += 1;
    else if (key === "--poll-seconds") args.pollSeconds = Number(next), i += 1;
    else if (key === "--help") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${key}`);
    }
  }
  return args;
}

function printHelp() {
  console.log(`Usage:
  node youzan_login_assist_cdp.js --mode status
  node youzan_login_assist_cdp.js --mode screenshot --output /tmp/youzan-login.png
  node youzan_login_assist_cdp.js --mode click-send-code
  node youzan_login_assist_cdp.js --mode fill-code --code 123456
  node youzan_login_assist_cdp.js --mode wait-login --wait-seconds 300

Modes:
  status          Detect whether Youzan backend API is currently logged in.
  screenshot      Capture the current Youzan/Chrome page for Feishu delivery.
  click-send-code Try to click a visible "send/get verification code" control.
  fill-code       Fill an SMS/login code into the likely verification input.
  wait-login      Poll until login succeeds or timeout.

Prerequisite:
  Start Chrome with --remote-debugging-port=9222.
`);
}

function requestJson(url, method = "GET") {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method }, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve(JSON.parse(data));
        } catch (error) {
          reject(error);
        }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function ensurePage(cdpBase, url) {
  const base = cdpBase.replace(/\/$/, "");
  let pages = await requestJson(`${base}/json/list`);
  let page = pages.find((p) => p.type === "page" && String(p.url || "").includes("youzan.com"));
  if (page) return page;

  try {
    await requestJson(`${base}/json/new?${encodeURIComponent(url)}`, "PUT");
  } catch (_) {
    // Some Chrome builds disable /json/new. Fall through and inspect pages again.
  }
  pages = await requestJson(`${base}/json/list`);
  page = pages.find((p) => p.type === "page" && String(p.url || "").includes("youzan.com")) || pages.find((p) => p.type === "page");
  if (!page) throw new Error("No Chrome page available through CDP.");
  return page;
}

async function connect(cdpBase, url) {
  const page = await ensurePage(cdpBase, url);
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const mid = ++id;
    pending.set(mid, { resolve, reject });
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const waiter = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? waiter.reject(new Error(JSON.stringify(msg.error))) : waiter.resolve(msg.result);
    }
  };
  await new Promise((resolve) => { ws.onopen = resolve; });
  await send("Page.enable");
  await send("Runtime.enable");
  return { ws, send };
}

async function evaluate(send, expression) {
  const result = await send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
    timeout: 60000,
  });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function navigate(send, url) {
  await send("Page.navigate", { url });
  await sleep(3000);
}

async function loginStatus(send) {
  return evaluate(send, `(async()=>{
    const out = { loggedIn: false, url: location.href, title: document.title, reason: "" };
    try {
      const r = await fetch("/v4/statcenter/custompeek/api/queryReport.json?page=1&pageSize=1", { credentials: "include" });
      const text = await r.text();
      let json = null;
      try { json = JSON.parse(text); } catch (_) {}
      if (json && json.code === 0) {
        out.loggedIn = true;
        out.reason = "custompeek api ok";
      } else {
        out.reason = json ? (json.msg || String(json.code)) : "non-json response";
      }
    } catch (error) {
      out.reason = String(error && error.message || error);
    }
    out.bodyHint = document.body ? document.body.innerText.slice(0, 120).replace(/\\s+/g, " ") : "";
    return out;
  })()`);
}

async function screenshot(send, output) {
  const dir = path.dirname(output);
  fs.mkdirSync(dir, { recursive: true });
  const result = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  fs.writeFileSync(output, Buffer.from(result.data, "base64"));
  return { saved: output, bytes: fs.statSync(output).size };
}

async function clickSendCode(send) {
  return evaluate(send, `(()=>{
    const visible = (el) => {
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return s.visibility !== "hidden" && s.display !== "none" && r.width > 0 && r.height > 0;
    };
    const candidates = [...document.querySelectorAll("button,a,[role=button],span,div")]
      .filter(visible)
      .map((el) => ({ el, text: (el.innerText || el.textContent || "").trim().replace(/\\s+/g, "") }))
      .filter((x) => x.text && /获取验证码|发送验证码|收取验证码|短信验证码|重新发送/.test(x.text));
    const picked = candidates.find((x) => /button/i.test(x.el.tagName) || x.el.getAttribute("role") === "button") || candidates[0];
    if (!picked) return { clicked: false, reason: "send-code control not found" };
    picked.el.click();
    return { clicked: true, text: picked.text };
  })()`);
}

async function fillCode(send, code, selector) {
  if (!/^[0-9A-Za-z]{4,8}$/.test(code)) throw new Error("Code must be 4-8 letters/digits.");
  return evaluate(send, `(()=>{
    const code = ${JSON.stringify(code)};
    const selector = ${JSON.stringify(selector)};
    const visible = (el) => {
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return !el.disabled && !el.readOnly && s.visibility !== "hidden" && s.display !== "none" && r.width > 0 && r.height > 0;
    };
    let inputs = selector ? [...document.querySelectorAll(selector)] : [...document.querySelectorAll("input")];
    inputs = inputs.filter(visible);
    const score = (el) => {
      const text = [el.placeholder, el.name, el.id, el.className, el.autocomplete, el.type].join(" ").toLowerCase();
      let s = 0;
      if (/验证码|校验码|短信|code|sms|verify|captcha/.test(text)) s += 10;
      if (String(el.maxLength || "").match(/^[4-8]$/)) s += 4;
      if (el.type === "tel" || el.inputMode === "numeric") s += 2;
      return s;
    };
    inputs.sort((a,b) => score(b) - score(a));
    const input = inputs[0];
    if (!input) return { filled: false, reason: "input not found" };
    input.focus();
    input.value = code;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    const submit = [...document.querySelectorAll("button,a,[role=button]")]
      .filter(visible)
      .find((el) => /登录|确认|提交|下一步|验证/.test((el.innerText || el.textContent || "").trim()));
    if (submit) submit.click();
    return { filled: true, submitted: Boolean(submit), inputHint: input.placeholder || input.name || input.id || input.type };
  })()`);
}

async function waitLogin(send, waitSeconds, pollSeconds) {
  const deadline = Date.now() + waitSeconds * 1000;
  let last = null;
  while (Date.now() < deadline) {
    last = await loginStatus(send);
    console.log(JSON.stringify({ loggedIn: last.loggedIn, reason: last.reason, url: last.url }));
    if (last.loggedIn) return last;
    await sleep(pollSeconds * 1000);
  }
  throw new Error(`Timed out waiting for login; last=${JSON.stringify(last)}`);
}

async function main() {
  const args = parseArgs(process.argv);
  const { ws, send } = await connect(args.cdp, args.url);
  try {
    if (args.mode !== "status") {
      const state = await loginStatus(send);
      if (!state.url.includes("youzan.com")) await navigate(send, args.url);
    }

    if (args.mode === "status") {
      console.log(JSON.stringify(await loginStatus(send), null, 2));
    } else if (args.mode === "screenshot") {
      console.log(JSON.stringify(await screenshot(send, args.output), null, 2));
    } else if (args.mode === "click-send-code") {
      console.log(JSON.stringify(await clickSendCode(send), null, 2));
    } else if (args.mode === "fill-code") {
      if (!args.code) throw new Error("--code is required for fill-code mode.");
      console.log(JSON.stringify(await fillCode(send, args.code, args.selector), null, 2));
    } else if (args.mode === "wait-login") {
      console.log(JSON.stringify(await waitLogin(send, args.waitSeconds, args.pollSeconds), null, 2));
    } else {
      throw new Error(`Unsupported mode: ${args.mode}`);
    }
  } finally {
    ws.close();
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
