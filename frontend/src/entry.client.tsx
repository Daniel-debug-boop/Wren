import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HydratedRouter } from "react-router/dom";
import "./index.css";

// Register service worker for PWA support
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {
      // Service worker registration failed — app still works without it
    });
  });
}

createRoot(document).render(
  <StrictMode>
    <HydratedRouter />
  </StrictMode>,
);
