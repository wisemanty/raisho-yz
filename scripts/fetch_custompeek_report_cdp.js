#!/usr/bin/env node

const fs = require("fs");
const http = require("http");
const https = require("https");
const path = require("path");

const DEFAULT_REPORT_NAME = "来处订单商品明细_yz_open_id";

function parseArgs(argv) {
  const args = {
    cdp: "http://127.0.0.1:9222",
    reportName: DEFAULT_REPORT_NAME,
    reportId: "",
    outputDir: process.cwd(),
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
    else if (key === "--wait-seconds") args.waitSeconds = Number(next), i += 1;
    else if (key === "--poll-seconds") args.pollSeconds = Number(next), i += 1;
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
    [--no-re-export]

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
