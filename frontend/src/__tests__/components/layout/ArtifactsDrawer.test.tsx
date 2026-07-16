import { describe, it, expect } from "vitest";
import { sanitizePreview } from "#/components/layout/ArtifactsDrawer";

describe("sanitizePreview", () => {
  it("strips script tags", () => {
    const out = sanitizePreview("<p>hi</p><script>alert(1)</script>");
    expect(out).not.toContain("<script>");
    expect(out).toContain("hi");
  });

  it("strips inline event handlers", () => {
    const out = sanitizePreview('<img src=x onerror="alert(1)">ok');
    expect(out.toLowerCase()).not.toContain("onerror");
    expect(out).toContain("ok");
  });

  it("keeps safe formatting", () => {
    const out = sanitizePreview("<b>bold</b> and <i>italic</i>");
    expect(out).toContain("<b>bold</b>");
    expect(out).toContain("<i>italic</i>");
  });
});
