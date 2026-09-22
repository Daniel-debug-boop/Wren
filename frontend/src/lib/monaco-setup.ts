import { loader } from "@monaco-editor/react";

/* ── Monaco loading strategy ──────────────────────────────────────────────
 * @monaco-editor/react defaults to fetching Monaco from a CDN at runtime.
 * That breaks self-hosted/offline deployments, and Monaco 0.55+'s CDN no
 * longer serves the AMD worker paths (vs/base/worker/workerMain.js was
 * removed from the distribution), so language workers 404 at runtime.
 *
 * Fix: serve the official pre-built AMD bundle from our own origin as
 * static assets (copied from node_modules by scripts/copy-monaco.mjs into
 * public/monaco). The AMD build is self-consistent — the editor bootstraps
 * its own web workers from the same directory, so syntax highlighting,
 * TypeScript IntelliSense, JSON tooling and validation all work, with zero
 * Vite bundle cost and no SSR complications.
 * ────────────────────────────────────────────────────────────────────────── */

loader.config({
  paths: { vs: "/monaco/vs" },
});

export {};
