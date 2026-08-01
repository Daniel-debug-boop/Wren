import { test, expect } from "@playwright/test";

/**
 * E2E smoke tests for the current Wren UI (amber dark theme).
 *
 * The backend is not required for these tests: pages render their shells
 * and API calls fail gracefully into empty/loading states. They cover the
 * critical user journeys: landing → navigation → the core product pages.
 */

test("landing page renders the hero and CTAs", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Ship production code/i }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: /Open Workspace/i }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Self-host Docs/i })).toBeVisible();
});

test("sidebar navigation reaches the core pages", async ({ page }) => {
  await page.goto("/generation");

  // Sidebar nav appears on internal pages
  await expect(page.getByRole("link", { name: "Generate" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Chat" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Settings" })).toBeVisible();
  await expect(page.getByRole("link", { name: "API Keys" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Skills" })).toBeVisible();

  // Navigate to Chat
  await page.getByRole("link", { name: "Chat" }).click();
  await expect(page).toHaveURL(/\/conversation/);
  await expect(page.getByRole("heading", { name: /Conversations/i })).toBeVisible();
});

test("generation page renders the pipeline UI", async ({ page }) => {
  await page.goto("/generation");
  await expect(
    page.getByRole("heading", { name: /AI Project Generator/i }),
  ).toBeVisible();
  await expect(
    page.getByPlaceholder(/Describe what you want to build/i),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /Generate Project/i })).toBeVisible();
});

test("settings page renders the LLM configuration", async ({ page }) => {
  await page.goto("/settings");
  await expect(
    page.getByRole("heading", { name: /Settings/i }),
  ).toBeVisible();
  await expect(page.getByLabel(/Provider/i)).toBeVisible();
  await expect(page.getByLabel(/API Key/i)).toBeVisible();
});

test("workspace renders the IDE shell", async ({ page }) => {
  await page.goto("/workspace");
  // Top bar with the Wren brand
  await expect(page.getByText("Wren", { exact: true }).first()).toBeVisible();
  // Chat input in the right panel
  await expect(page.getByPlaceholder(/Type your prompt/i)).toBeVisible();
  // Monaco editor container
  await expect(page.locator(".monaco-editor").first()).toBeVisible();
});
