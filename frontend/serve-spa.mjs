import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BUILD_DIR = path.join(__dirname, "build");
const PORT = 3000;

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".mjs": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".webp": "image/webp",
  ".avif": "image/avif",
};

/* ── Mock API Responses ── */
const MOCK_API = {
  "/api/config": {
    app_mode: "oss",
    providers_configured: ["github", "gitlab"],
    text_llm: { model: "gpt-4o", provider: "openai" },
    title: "Wren",
  },
  "/api/settings": {
    llm_api_key: "sk-••••••••",
    llm_model: "gpt-4o",
    llm_provider: "openai",
    theme: "dark",
  },
  "/api/git/repositories": {
    items: [
      {
        id: "1",
        full_name: "user/my-project",
        owner: "user",
        name: "my-project",
        provider: "github",
        url: "https://github.com/user/my-project",
      },
      {
        id: "2",
        full_name: "user/awesome-app",
        owner: "user",
        name: "awesome-app",
        provider: "github",
        url: "https://github.com/user/awesome-app",
      },
    ],
  },
  "/api/git/branches": {
    items: [
      { name: "main", commit_sha: "abc123", protected: true },
      { name: "develop", commit_sha: "def456", protected: false },
      { name: "feature/new-ui", commit_sha: "ghi789", protected: false },
    ],
  },
  "/api/users/me": {
    id: "1",
    email: "demo@wren.ai",
    name: "Demo User",
    avatar_url: null,
  },
};

function mockApiResponse(urlPath) {
  // Check exact match
  if (MOCK_API[urlPath]) {
    return { status: 200, body: JSON.stringify(MOCK_API[urlPath]) };
  }

  // Check /api/git/* patterns
  if (urlPath.startsWith("/api/git/") && urlPath.includes("/branches")) {
    return { status: 200, body: JSON.stringify(MOCK_API["/api/git/branches"]) };
  }

  // Generic api fallback
  if (urlPath.startsWith("/api/")) {
    return { status: 200, body: JSON.stringify({}) };
  }

  return null;
}

// ── Dynamically discover CSS files at startup ──
// CSS filenames contain content hashes that change on every build.
// Scanning avoids hardcoding fragile filenames.
const CSS_FILES = (() => {
  try {
    return fs.readdirSync(path.join(BUILD_DIR, "assets"))
      .filter((f) => f.endsWith(".css"))
      .map((f) => `/assets/${f}`);
  } catch {
    return [];
  }
})();

const server = http.createServer((req, res) => {
  const urlPath = new URL(req.url, `http://${req.headers.host}`).pathname;

  // ── Mock API handler ──
  if (urlPath.startsWith("/api/")) {
    const mock = mockApiResponse(urlPath);
    if (mock) {
      res.writeHead(mock.status, {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      });
      res.end(mock.body);
    } else {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({}));
    }
    return;
  }

  // ── Static file serving with SPA fallback ──
  let servingPath = urlPath;

  // SPA fallback: no extension → serve index.html
  const rawExt = path.extname(servingPath).toLowerCase();
  if (!rawExt || servingPath === "/") {
    servingPath = "/index.html";
  }

  const filePath = path.join(BUILD_DIR, servingPath);

  // Security: prevent path traversal
  if (!filePath.startsWith(BUILD_DIR)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      if (err.code === "ENOENT") {
        res.writeHead(404);
        res.end("Not Found");
      } else {
        res.writeHead(500);
        res.end("Internal Server Error");
      }
      return;
    }

    // Compute MIME type from the actual served file
    const fileExt = path.extname(servingPath).toLowerCase();
    const contentType = MIME_TYPES[fileExt] || "application/octet-stream";

    let body = data;

    // ── Inject missing stylesheet links into index.html ──
    // React Router v7 SPA build produces HTML with NO <link rel="stylesheet"> tags.
    // CSS files exist on disk but the browser never applies them.
    // We inject the links dynamically here.
    if (servingPath === "/index.html" && CSS_FILES.length > 0) {
      const html = data.toString("utf-8");
      const styleLinks = CSS_FILES
        .map((href) => `    <link rel="stylesheet" href="${href}" />`)
        .join("\n");
      // Inject right before </head> — robust against title tag changes
      const injected = html.replace(
        "</head>",
        `${styleLinks}\n  </head>`,
      );
      body = Buffer.from(injected, "utf-8");
    }

    res.writeHead(200, {
      "Content-Type": contentType,
      "Cache-Control": "no-cache",
    });
    res.end(body);
  });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`\n  ✦ WREN — PREVIEW SERVER`);
  console.log(`  ───────────────────────`);
  console.log(`  ➜  http://localhost:${PORT}/`);
  console.log(`  ✦ Mock API enabled\n`);
});
