#!/usr/bin/env node

/**
 * Wren — Custom Production Server
 *
 * A custom Express server that:
 *   1. Serves static assets from the build directory with proper caching
 *   2. Uses @react-router/express for SSR on non-asset routes
 *   3. Binds to 0.0.0.0 for container/cloud deployments
 *   4. Reads PORT from environment (Freebuff injects this)
 */

import fs from "node:fs";
import path from "node:path";
import url from "node:url";
import os from "node:os";

import compression from "compression";
import express from "express";
import morgan from "morgan";
import sourceMapSupport from "source-map-support";
import { createRequestHandler } from "@react-router/express";

/* ── Source maps in production ── */
sourceMapSupport.install({
  retrieveSourceMap(source) {
    if (source.startsWith("file://")) {
      const sourceMapPath = `${url.fileURLToPath(source)}.map`;
      if (fs.existsSync(sourceMapPath)) {
        return { url: source, map: fs.readFileSync(sourceMapPath, "utf8") };
      }
    }
    return null;
  },
});

/* ── Configuration ── */
const PORT = parseInt(process.env.PORT || "3001", 10);
const HOST = process.env.HOST || "0.0.0.0";

const __filename = url.fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BUILD_DIR = path.resolve(__dirname, "build");
const SERVER_BUILD = path.resolve(BUILD_DIR, "server", "index.js");

/* ── Bootstrap Express ── */
const app = express();
app.disable("x-powered-by");
app.use(compression());

/* ── Static asset middleware (MUST come before SSR handler) ── */

// 1. Immutable cache for hashed assets from BOTH client and server builds
//    (React Router SSR may reference server-build assets with different hashes)
app.use(
  "/assets",
  express.static(path.join(BUILD_DIR, "server", "assets"), {
    immutable: true,
    maxAge: "1y",
  }),
);
app.use(
  "/assets",
  express.static(path.join(BUILD_DIR, "assets"), {
    immutable: true,
    maxAge: "1y",
  }),
);

// 2. Short-lived cache for the rest of build/ (root files like favicon, manifest, etc.)
app.use(express.static(BUILD_DIR, { maxAge: "1h" }));

// 3. Public directory (if it exists)
app.use(express.static(path.resolve(__dirname, "public"), { maxAge: "1h" }));

/* ── Request logging ── */
app.use(morgan("tiny"));

/* ── React Router SSR handler (catch-all) ── */
const build = await import(url.pathToFileURL(SERVER_BUILD).href);

app.all(
  "/{*splat}",
  createRequestHandler({
    build,
    mode: process.env.NODE_ENV || "production",
  }),
);

/* ── Start server ── */
app.listen(PORT, HOST, () => {
  // Find a non-internal IPv4 address to show
  const address =
    process.env.HOST ||
    Object.values(os.networkInterfaces())
      .flat()
      .find(
        (ip) =>
          ip &&
          String(ip.family).includes("4") &&
          !ip.internal,
      )?.address;

  const url = address
    ? `http://localhost:${PORT} (http://${address}:${PORT})`
    : `http://localhost:${PORT}`;

  console.log(`[wren-server] ${url}`);
  console.log(`[wren-server] static: ${BUILD_DIR}`);
  console.log(`[wren-server] ssr:    ${SERVER_BUILD}`);
});
