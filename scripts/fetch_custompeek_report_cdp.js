#!/usr/bin/env node

const fs = require("fs");
const http = require("http");
const https = require("https");
const path = require("path");

const DEFAULT_REPORT_NAME = "来处订单商品明细_yz_open_id";
const DEFAULT_SHOP_NAME = "RAISHO来处";

function parseArgs(argv) {
  const args = {
    cdp: "http://127.0.0.1:9222",
    reportName: DEFAULT_REPORT_NAME,
    reportId: "",
    outputDir: process.cwd(),
    shopName: DEFAULT_SHOP_NAME,
    autoSelectShop: true,
    reExport: true,
    waitSeconds: 900,
    pollSeconds: 10,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i];
    const next = argv[i + 1];
    if (key === "--cdp") args.cdp = next, i += 1;
    else if (key === "--report-name") args.reportName = next, i += 1;
    else if (key === "--report-id") args.reportId = next, i += 1;
    else if (key === "--output-dir") args.outputDir = next, i += 1;
    else if (key === "--shop-name") args.shopName = next, i += 1;
    else if (key === "--wait-seconds") args.waitSeconds = Number(next), i += 1;
    else if (key === "--poll-seconds") args.pollSeconds = Number(next), i += 1;
    else if (key === "--no-auto-select-shop") args.autoSelectShop = false;
    else if (key === "--no-re-export") args.reExport = false;
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
  node fetch_custompeek_report_cdp.js \\
    --output-dir "/path/to/raw-data" \\
    [--report-name "${DEFAULT_REPORT_NAME}"] \\
    [--report-id 436628] \\
    [--cdp http://127.0.0.1:9222] \\
    [--shop-name "${DEFAULT_SHOP_NAME}"] \\
    [--no-re-export]
    [--no-auto-select-shop]

Prerequisite:
  Start Chrome with --remote-debugging-port=9222 and log in to Youzan.
`);
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    http
      .get(url, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (error) {
            reject(error);
          }
        });
      })
      .on("error", reject);
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function download(url, outFile) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(outFile);
    https
      .get(url, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          file.close();
          fs.rmSync(outFile, { force: true });
          resolve(download(res.headers.location, outFile));
          return;
        }
        if (res.statusCode !== 200) {
          file.close();
          fs.rmSync(outFile, { force: true });
          reject(new Error(`Download failed with status ${res.statusCode}`));
          return;
        }
        res.pipe(file);
        file.on("finish", () => {
          file.close(() => resolve({
            bytes: fs.statSync(outFile).size,
            contentType: res.headers["content-type"] || "",
          }));
        });
      })
      .on("error", (error) => {
        file.close();
        fs.rmSync(outFile, { force: true });
        reject(error);
      });
  });
}

async function connect(cdpBase) {
  const pages = await getJson(`${cdpBase.replace(/\/$/, "")}/json/list`);
  const page = pages.find((p) => p.type === "page" && String(p.url || "").includes("youzan.com"));
  if (!page) throw new Error("No Youzan page found in Chrome DevTools Protocol. Open Youzan and log in first.");

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
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
  return result.result.value;
}

function browserExpression(inner) {
  return `(async()=>{${inner}})()`;
}

async function youzanGet(send, url) {
  return evaluate(send, browserExpression(`
    const r = await fetch(${JSON.stringify(url)}, { credentials: "include" });
    return await r.json();
  `));
}

async function youzanPost(send, url, payload) {
  return evaluate(send, browserExpression(`
    const csrf = (window._global && window._global.csrf_token) || "";
    const body = new URLSearchParams({ ...${JSON.stringify(payload)}, csrf_token: csrf }).toString();
    const r = await fetch(${JSON.stringify(url)}, {
      method: "POST",
      credentials: "include",
      headers: {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest"
      },
      body
    });
    return await r.json();
  `));
}

async function currentPage(send) {
  return evaluate(send, browserExpression(`
    return {
      url: location.href,
      title: document.title,
      bodyHint: document.body ? document.body.innerText.slice(0, 300).replace(/\\s+/g, " ") : ""
    };
  `));
}

async function clickAt(send, x, y) {
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y, button: "none" });
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
}

async function selectShopIfNeeded(send, shopName) {
  const before = await currentPage(send);
  if (!before.title.includes("选择店铺") && !before.bodyHint.includes("进入工作台")) {
    return { selected: false, reason: "not_on_shop_select", page: before };
  }

  const target = await evaluate(send, browserExpression(`
    const shopName = ${JSON.stringify(shopName)};
    const visible = (el) => {
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return s.visibility !== "hidden" && s.display !== "none" && r.width > 0 && r.height > 0;
    };
    const containers = [...document.querySelectorAll("div,section,li")]
      .filter(visible)
      .filter((el) => (el.innerText || "").includes(shopName) && (el.innerText || "").includes("进入工作台"));
    const root = containers.sort((a,b) => a.getBoundingClientRect().width - b.getBoundingClientRect().width)[0] || document.body;
    const buttons = [...root.querySelectorAll("button,a,[role=button],div,span")]
      .filter(visible)
      .filter((el) => /进入工作台/.test((el.innerText || el.textContent || "").trim()));
    const picked = buttons.sort((a,b) => {
      const ar = a.getBoundingClientRect();
      const br = b.getBoundingClientRect();
      return (ar.width * ar.height) - (br.width * br.height);
    })[0];
    if (!picked) return { found: false, reason: "workbench_button_not_found", title: document.title, bodyHint: document.body.innerText.slice(0, 200) };
    const r = picked.getBoundingClientRect();
    return { found: true, x: r.left + r.width / 2, y: r.top + r.height / 2, text: (picked.innerText || picked.textContent || "").trim(), title: document.title };
  `));
  if (!target.found) return { selected: false, ...target };

  await clickAt(send, target.x, target.y);
  await sleep(5000);
  const after = await currentPage(send);
  return { selected: true, target, page: after };
}

async function ensureCustompeekPage(send, shopName, autoSelectShop) {
  if (autoSelectShop) {
    const selection = await selectShopIfNeeded(send, shopName);
    if (selection.selected) console.log(JSON.stringify({ autoSelectShop: true, shopName, page: selection.page }));
  }
  const page = await currentPage(send);
  if (!page.url.includes("/v4/statcenter/custompeek/index")) {
    await send("Page.navigate", { url: "https://www.youzan.com/v4/statcenter/custompeek/index" });
    await sleep(3000);
  }
}

async function findReport(send, reportName, reportId) {
  if (reportId) {
    const byId = await youzanGet(send, `/v4/statcenter/custompeek/api/queryReportById.json?reportId=${encodeURIComponent(reportId)}`);
    if (byId.code !== 0 || !byId.data) throw new Error(`Report id ${reportId} not found: ${byId.msg || byId.code}`);
    return byId.data;
  }

  const list = await youzanGet(send, `/v4/statcenter/custompeek/api/queryReport.json?page=1&pageSize=20&reportName=${encodeURIComponent(reportName)}`);
  const items = list && list.data && Array.isArray(list.data.items) ? list.data.items : [];
  const report = items.find((item) => item.reportName === reportName) || items[0];
  if (!report) throw new Error(`Report not found: ${reportName}`);
  return report;
}

async function pollUntilReady(send, reportId, waitSeconds, pollSeconds) {
  const deadline = Date.now() + waitSeconds * 1000;
  let last = null;
  while (Date.now() < deadline) {
    const res = await youzanGet(send, `/v4/statcenter/custompeek/api/queryReportById.json?reportId=${encodeURIComponent(reportId)}`);
    if (res.code !== 0 || !res.data) throw new Error(`Polling failed: ${res.msg || res.code}`);
    last = res.data;
    console.log(JSON.stringify({
      reportId,
      status: last.status,
      updatedTime: last.updatedTime,
      downloadCount: Array.isArray(last.downloadLogList) ? last.downloadLogList.length : 0,
    }));

    // Observed mapping: 1 = executing in the UI, 2 = completed/downloadable.
    if (last.status === 2) return last;
    if (last.status !== 0 && last.status !== 1) return last;
    await sleep(pollSeconds * 1000);
  }
  throw new Error(`Timed out waiting for report ${reportId}; last status=${last && last.status}`);
}

function safeFileName(name) {
  return name.replace(/[\\/:*?"<>|]/g, "_");
}

async function main() {
  const args = parseArgs(process.argv);
  fs.mkdirSync(args.outputDir, { recursive: true });

  const { ws, send } = await connect(args.cdp);
  try {
    await ensureCustompeekPage(send, args.shopName, args.autoSelectShop);
    const report = await findReport(send, args.reportName, args.reportId);
    const reportId = String(report.id);
    console.log(JSON.stringify({
      found: true,
      reportId,
      reportName: report.reportName,
      model: report.dataModel && report.dataModel.modelName,
      status: report.status,
    }));

    if (args.reExport) {
      const reExport = await youzanPost(send, "/v4/statcenter/custompeek/api/reExport.json", { reportId });
      if (reExport.code !== 0) throw new Error(`reExport failed: ${reExport.msg || reExport.code}`);
      console.log(JSON.stringify({ reExport: true, reportId }));
    }

    const ready = await pollUntilReady(send, reportId, args.waitSeconds, args.pollSeconds);
    if (ready.status !== 2) throw new Error(`Report is not downloadable; status=${ready.status}`);

    const downloadInfo = await youzanPost(send, "/v4/statcenter/custompeek/api/getDownload.json", { reportId });
    if (downloadInfo.code !== 0 || !downloadInfo.data || !downloadInfo.data.url) {
      throw new Error(`getDownload failed: ${downloadInfo.msg || downloadInfo.code}`);
    }

    const tmpFile = path.join(args.outputDir, `${safeFileName(ready.reportName || args.reportName)}.tmp`);
    const meta = await download(downloadInfo.data.url, tmpFile);
    const magic = fs.readFileSync(tmpFile).subarray(0, 4).toString("hex");
    const ext = magic === "504b0304" ? ".xlsx" : ".csv";
    const finalFile = path.join(args.outputDir, `${safeFileName(ready.reportName || args.reportName)}${ext}`);
    fs.renameSync(tmpFile, finalFile);

    console.log(JSON.stringify({
      saved: finalFile,
      bytes: meta.bytes,
      contentType: meta.contentType,
      detectedExt: ext,
    }));
  } finally {
    ws.close();
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
