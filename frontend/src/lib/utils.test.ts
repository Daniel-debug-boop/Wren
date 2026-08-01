import { describe, it, expect } from "vitest";
import { cn, formatRelativeTime } from "./utils";

describe("cn", () => {
  it("joins truthy class names", () => {
    expect(cn("a", "b", "c")).toBe("a b c");
  });

  it("filters out falsy values", () => {
    expect(cn("a", false, undefined, null, "", "b")).toBe("a b");
  });

  it("merges tailwind conflicts (last wins)", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("bg-red-500", "bg-blue-500")).toBe("bg-blue-500");
  });

  it("accepts objects and arrays", () => {
    expect(cn({ a: true, b: false }, ["c", "d"])).toBe("a c d");
  });
});

describe("formatRelativeTime", () => {
  it("returns 'just now' for recent timestamps", () => {
    expect(formatRelativeTime(Date.now() - 5_000)).toBe("just now");
  });

  it("returns minutes ago", () => {
    expect(formatRelativeTime(Date.now() - 5 * 60 * 1000)).toBe("5m ago");
  });

  it("returns hours ago", () => {
    expect(formatRelativeTime(Date.now() - 3 * 60 * 60 * 1000)).toBe("3h ago");
  });

  it("returns days ago", () => {
    expect(formatRelativeTime(Date.now() - 2 * 24 * 60 * 60 * 1000)).toBe(
      "2d ago",
    );
  });

  it("falls back to a date for very old timestamps", () => {
    const d = new Date("2020-01-01T00:00:00Z");
    expect(formatRelativeTime(d)).toBe(d.toLocaleDateString());
  });
});
