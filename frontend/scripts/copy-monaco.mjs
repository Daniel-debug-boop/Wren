#!/usr/bin/env node
/**
 * Copies Monaco Editor's pre-built AMD bundle from node_modules into
 * public/monaco so it is served as static assets (dev) and included in
 * the build output (production).
 *
 * Why: @monaco-editor/react defaults to fetching Monaco from a CDN at
 * runtime, which (a) breaks self-hosted/offline deployments and (b) 404s
 * on Monaco 0.55+ because the CDN no longer serves the AMD worker paths
 * (vs/base/worker/workerMain.js was removed from the distribution).
 * Serving the versioned AMD build locally fixes both, with zero bundle
 * cost — files are plain static assets, never processed by Vite.
 */
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const src = join(root, "node_modules", "monaco-editor", "min");
const dest = join(root, "public", "monaco");

if (!existsSync(src)) {
  console.error("[copy-monaco] monaco-editor not installed — run npm install first");
  process.exit(1);
}

rmSync(dest, { recursive: true, force: true });
mkdirSync(dest, { recursive: true });
cpSync(src, dest, { recursive: true });
console.log("[copy-monaco] copied monaco-editor -> public/monaco");
