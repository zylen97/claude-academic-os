#!/usr/bin/env node

import fs from 'node:fs/promises';
import { constants as fsConstants } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';

const PROXY_BASE = 'http://localhost:3456';
const ADVANCED_SEARCH_URL = 'https://webofscience.clarivate.cn/wos/woscc/advanced-search';
const USAGE_SORT_LABEL = 'Usage (last 180 days): most first';

function parseArgs(argv) {
  const args = {
    mode: 'count',
    limit: 1000,
    timeoutMs: 60000,
    downloadDir: path.join(os.homedir(), 'Downloads'),
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--mode') args.mode = argv[++i];
    else if (arg === '--output') args.output = argv[++i];
    else if (arg === '--limit') args.limit = Number(argv[++i]);
    else if (arg === '--timeout-ms') args.timeoutMs = Number(argv[++i]);
    else if (arg === '--download-dir') args.downloadDir = path.resolve(argv[++i]);
    else if (arg === '--help' || arg === '-h') args.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if (!['count', 'export'].includes(args.mode)) {
    throw new Error('--mode must be count or export');
  }
  if (!Number.isInteger(args.limit) || args.limit < 1 || args.limit > 1000) {
    throw new Error('--limit must be an integer between 1 and 1000');
  }
  if (!Number.isInteger(args.timeoutMs) || args.timeoutMs < 5000) {
    throw new Error('--timeout-ms must be an integer >= 5000');
  }
  if (args.mode === 'export') {
    if (!args.output) throw new Error('--output is required in export mode');
    args.output = path.resolve(args.output);
    if (!args.output.toLowerCase().endsWith('.ris')) {
      throw new Error('--output must end with .ris');
    }
  }
  return args;
}

function printHelp() {
  process.stdout.write(`Usage:
  wos_cdp_export.mjs --mode count < query.txt
  wos_cdp_export.mjs --mode export --output /absolute/structure/2_literature/direction1_wos.ris [--limit 1000] < query.txt

The script always applies SCIE + SSCI and Usage (last 180 days): most first.
`);
}

async function readQuery() {
  let query = '';
  for await (const chunk of process.stdin) query += chunk;
  query = query.trim();
  if (!query) throw new Error('WoS query is required on stdin');
  return query;
}

async function requestJson(pathname, { method = 'GET', body, params } = {}) {
  const url = new URL(pathname, PROXY_BASE);
  for (const [key, value] of Object.entries(params || {})) url.searchParams.set(key, value);
  const response = await fetch(url, {
    method,
    body,
    headers: body === undefined ? undefined : { 'content-type': 'text/plain; charset=utf-8' },
  });
  const raw = await response.text();
  if (!response.ok) throw new Error(`${method} ${url.pathname} failed (${response.status}): ${raw}`);
  try {
    return JSON.parse(raw);
  } catch {
    throw new Error(`${method} ${url.pathname} returned non-JSON: ${raw.slice(0, 300)}`);
  }
}

async function evalJs(targetId, expression) {
  const result = await requestJson('/eval', {
    method: 'POST',
    params: { target: targetId },
    body: expression,
  });
  if (result.error) throw new Error(`CDP eval failed: ${result.error}`);
  return result.value;
}

async function click(targetId, selector) {
  const result = await requestJson('/click', {
    method: 'POST',
    params: { target: targetId },
    body: selector,
  });
  if (!result.clicked) throw new Error(`Could not click selector: ${selector}`);
  return result;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitFor(description, fn, timeoutMs, intervalMs = 500) {
  const deadline = Date.now() + timeoutMs;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const value = await fn();
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await sleep(intervalMs);
  }
  const suffix = lastError ? `; last error: ${lastError.message}` : '';
  throw new Error(`Timed out waiting for ${description}${suffix}`);
}

async function pageState(targetId) {
  return evalJs(
    targetId,
    `(() => {
      const text = document.body?.innerText || '';
      const match = text.match(/([\\d,]+)\\s+results from Web of Science Core Collection/);
      return {
        title: document.title,
        url: location.href,
        ready: document.readyState,
        count: match ? Number(match[1].replace(/,/g, '')) : null,
        sort: (document.querySelector('#selectSortOption')?.innerText || '').replace(/\\s+/g, ' ').trim(),
        refined: text.includes('Refined By:') && text.includes('Web of Science Index:')
      };
    })()`,
  );
}

async function submitQuery(targetId, query, timeoutMs) {
  await waitFor(
    'WoS advanced-search editor',
    () => evalJs(targetId, `Boolean(document.querySelector('#advancedSearchInputArea'))`),
    timeoutMs,
  );
  const value = await evalJs(
    targetId,
    `(() => {
      const editor = document.querySelector('#advancedSearchInputArea');
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      setter.call(editor, ${JSON.stringify(query)});
      editor.dispatchEvent(new Event('input', { bubbles: true }));
      editor.dispatchEvent(new Event('change', { bubbles: true }));
      return editor.value;
    })()`,
  );
  if (value !== query) throw new Error('WoS query editor did not retain the full query');
  await click(targetId, 'button[data-ta="run-search"]');
  return waitFor(
    'WoS search results',
    async () => {
      const state = await pageState(targetId);
      return state.url.includes('/summary/') && Number.isInteger(state.count) ? state : null;
    },
    timeoutMs,
  );
}

async function applyScieSsci(targetId, timeoutMs) {
  await click(targetId, 'button[aria-controls="filter-section-EDN"]');
  const options = await waitFor(
    'Web of Science Index options',
    () => evalJs(
      targetId,
      `(() => {
        const nodes = [...document.querySelectorAll('#filter-section-EDN input[name="EDN"]')];
        if (!nodes.length) return null;
        return nodes.map((node) => ({ value: node.value, checked: node.checked, aria: node.getAttribute('aria-label') }));
      })()`,
    ),
    timeoutMs,
  );

  const selected = [];
  for (const option of options) {
    if (!['EDN.WOS.SCI', 'EDN.WOS.SSCI'].includes(option.value) && option.checked) {
      await click(targetId, `#filter-section-EDN input[value="${option.value}"]`);
    }
  }
  for (const value of ['EDN.WOS.SCI', 'EDN.WOS.SSCI']) {
    const option = options.find((item) => item.value === value);
    if (!option) continue;
    if (!option.checked) await click(targetId, `#filter-section-EDN input[value="${value}"]`);
    selected.push(value);
  }
  if (!selected.length) throw new Error('Neither SCIE nor SSCI is available in the WoS Index filter');

  const before = await pageState(targetId);
  await click(targetId, '#filter-section-EDN button[data-ta="refine-submit"]');
  const after = await waitFor(
    'SCIE + SSCI refine result',
    async () => {
      const state = await pageState(targetId);
      return state.url !== before.url && state.refined && Number.isInteger(state.count) ? state : null;
    },
    timeoutMs,
  );
  return { state: after, availableIndexes: options, selectedIndexes: selected };
}

async function ensureUsageSort(targetId, timeoutMs) {
  let state = await pageState(targetId);
  if (state.sort !== USAGE_SORT_LABEL) {
    await click(targetId, '#selectSortOption');
    await waitFor(
      'Usage (last 180 days) sort option',
      () => evalJs(targetId, `Boolean(document.querySelector('#usage-count-180-descending'))`),
      timeoutMs,
    );
    await click(targetId, '#usage-count-180-descending');
    state = await waitFor(
      'Usage (last 180 days) sort order',
      async () => {
        const next = await pageState(targetId);
        return next.sort === USAGE_SORT_LABEL && next.url.includes('/usage-count-180-descending/') ? next : null;
      },
      timeoutMs,
    );
  }
  return state;
}

async function snapshotRis(directory) {
  const snapshot = new Map();
  let entries = [];
  try {
    entries = await fs.readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.toLowerCase().endsWith('.ris')) continue;
    const filePath = path.join(directory, entry.name);
    const stat = await fs.stat(filePath);
    snapshot.set(filePath, { mtimeMs: stat.mtimeMs, size: stat.size });
  }
  return snapshot;
}

async function waitForDownloadedRis(directory, baseline, startedAt, timeoutMs) {
  let stablePath = null;
  let stableSize = -1;
  let stableChecks = 0;
  return waitFor(
    'completed RIS download',
    async () => {
      const current = await snapshotRis(directory);
      const candidates = [];
      for (const [filePath, stat] of current) {
        const old = baseline.get(filePath);
        const changed = !old || old.mtimeMs !== stat.mtimeMs || old.size !== stat.size;
        if (changed && stat.mtimeMs >= startedAt - 1500 && stat.size > 0) {
          candidates.push({ filePath, ...stat });
        }
      }
      candidates.sort((a, b) => b.mtimeMs - a.mtimeMs);
      const candidate = candidates[0];
      if (!candidate) return null;
      if (candidate.filePath === stablePath && candidate.size === stableSize) stableChecks += 1;
      else {
        stablePath = candidate.filePath;
        stableSize = candidate.size;
        stableChecks = 0;
      }
      return stableChecks >= 2 ? candidate : null;
    },
    timeoutMs,
    750,
  );
}

function countRisRecords(content) {
  const normalized = content.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n');
  const ty = (normalized.match(/^TY  - /gm) || []).length;
  const er = (normalized.match(/^ER  -\s*$/gm) || []).length;
  return { ty, er };
}

async function moveWithoutOverwrite(source, destination) {
  await fs.mkdir(path.dirname(destination), { recursive: true });
  try {
    await fs.copyFile(source, destination, fsConstants.COPYFILE_EXCL);
  } catch (error) {
    if (error.code === 'EEXIST') {
      throw new Error(`Target already exists; refusing to overwrite: ${destination}`);
    }
    throw error;
  }
  await fs.unlink(source);
}

function failurePath(output, actual, expected) {
  const stem = output.toLowerCase().endsWith('.ris') ? output.slice(0, -4) : output;
  return `${stem}.FAILED-${actual}-of-${expected}.ris`;
}

async function exportRis(targetId, count, args) {
  const exportCount = Math.min(count, args.limit, 1000);
  if (exportCount < 1) throw new Error('Cannot export an empty result set');

  try {
    await fs.access(args.output);
    throw new Error(`Target already exists; refusing to overwrite: ${args.output}`);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }

  await fs.mkdir(args.downloadDir, { recursive: true });
  const baseline = await snapshotRis(args.downloadDir);
  const startedAt = Date.now();

  await click(targetId, '#export-trigger-btn');
  await waitFor(
    'RIS export menu option',
    () => evalJs(targetId, `Boolean(document.querySelector('#exportToRisButton'))`),
    args.timeoutMs,
  );
  await click(targetId, '#exportToRisButton');
  await waitFor(
    'RIS export form',
    () => evalJs(targetId, `Boolean(document.querySelector('input[name="outputMethodType"][value="fromRange"]'))`),
    args.timeoutMs,
  );
  await click(targetId, 'input[name="outputMethodType"][value="fromRange"]');
  const range = await evalJs(
    targetId,
    `(() => {
      const setValue = (selector, value) => {
        const input = document.querySelector(selector);
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(input, String(value));
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        return input.value;
      };
      return {
        from: setValue('input[name="markFrom"]', 1),
        to: setValue('input[name="markTo"]', ${exportCount})
      };
    })()`,
  );
  if (range.from !== '1' || range.to !== String(exportCount)) {
    throw new Error(`WoS export range mismatch: ${JSON.stringify(range)}`);
  }

  await click(targetId, 'form wos-select button[role="combobox"]');
  await waitFor(
    'Full Record export option',
    () => evalJs(targetId, `Boolean(document.querySelector('#option-fullRecord'))`),
    args.timeoutMs,
  );
  await click(targetId, '#option-fullRecord');
  const contentLabel = await evalJs(
    targetId,
    `(document.querySelector('form wos-select button[role="combobox"]')?.innerText || '').trim()`,
  );
  if (contentLabel !== 'Full Record') throw new Error(`Unexpected record content: ${contentLabel}`);

  await click(targetId, '#exportButton');
  const downloaded = await waitForDownloadedRis(args.downloadDir, baseline, startedAt, args.timeoutMs);
  const content = await fs.readFile(downloaded.filePath, 'utf8');
  const records = countRisRecords(content);

  if (records.ty !== exportCount || records.er !== exportCount) {
    const failed = failurePath(args.output, Math.min(records.ty, records.er), exportCount);
    await moveWithoutOverwrite(downloaded.filePath, failed);
    throw new Error(
      `RIS record mismatch: expected ${exportCount}, TY=${records.ty}, ER=${records.er}; renamed to ${failed}`,
    );
  }

  await moveWithoutOverwrite(downloaded.filePath, args.output);
  return {
    output: args.output,
    records: exportCount,
    ty: records.ty,
    er: records.er,
    bytes: downloaded.size,
    renamedImmediately: true,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }
  const query = await readQuery();
  if (args.mode === 'export') {
    try {
      await fs.access(args.output);
      throw new Error(`Target already exists; refusing to overwrite: ${args.output}`);
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }

  await requestJson('/health');
  let targetId;
  try {
    const created = await requestJson('/new', { params: { url: ADVANCED_SEARCH_URL } });
    targetId = created.targetId;
    if (!targetId) throw new Error('CDP proxy did not return a targetId');

    const raw = await submitQuery(targetId, query, args.timeoutMs);
    const refined = await applyScieSsci(targetId, args.timeoutMs);
    const sorted = await ensureUsageSort(targetId, args.timeoutMs);
    const result = {
      mode: args.mode,
      query,
      rawHits: raw.count,
      actualHits: refined.state.count,
      selectedIndexes: refined.selectedIndexes,
      sort: sorted.sort,
      resultUrl: sorted.url,
    };
    if (args.mode === 'export') {
      result.export = await exportRis(targetId, refined.state.count, args);
    }
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } finally {
    if (targetId) {
      try {
        await requestJson('/close', { params: { target: targetId } });
      } catch (error) {
        process.stderr.write(`WARNING: failed to close background tab: ${error.message}\n`);
      }
    }
  }
}

main().catch((error) => {
  process.stderr.write(`ERROR: ${error.message}\n`);
  process.exitCode = 1;
});
