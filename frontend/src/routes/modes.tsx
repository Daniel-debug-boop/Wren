/* Custom mode creator page — users define their own modes */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { MODES, type ModeDef } from "#/types/mode";

const STORAGE_KEY = "wren-custom-modes";

interface CustomMode {
  id: string;
  label: string;
  shortLabel: string;
  description: string;
  icon: string;
  systemPrompt: string;
  suggestOn: string[];
  color?: string;
}

function loadCustomModes(): CustomMode[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveCustomModes(modes: CustomMode[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(modes));
}

const ICON_OPTIONS = [
  {
    value: "wrench",
    label: "Wrench",
    svg: "M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z",
  },
  { value: "zap", label: "Zap", svg: "M13 2L3 14h9l-1 8 10-12h-9l1-8z" },
  {
    value: "search",
    label: "Search",
    svg: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  },
  {
    value: "star",
    label: "Star",
    svg: "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
  },
  {
    value: "shield",
    label: "Shield",
    svg: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  },
  { value: "hash", label: "Hash", svg: "M4 9h16M4 15h16M10 3L8 21M16 3l-2 18" },
  {
    value: "layers",
    label: "Layers",
    svg: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
  },
  { value: "terminal", label: "Terminal", svg: "M4 17l6-6-6-6M12 19h8" },
];

export default function ModesPage() {
  const navigate = useNavigate();
  const [customModes, setCustomModes] = useState<CustomMode[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  /* Form state */
  const [formLabel, setFormLabel] = useState("");
  const [formShortLabel, setFormShortLabel] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formIcon, setFormIcon] = useState("wrench");
  const [formSystemPrompt, setFormSystemPrompt] = useState("");
  const [formSuggestOn, setFormSuggestOn] = useState("");
  const [formColor, setFormColor] = useState("#E86C4A");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    setCustomModes(loadCustomModes());
  }, []);

  function resetForm() {
    setFormLabel("");
    setFormShortLabel("");
    setFormDescription("");
    setFormIcon("wrench");
    setFormSystemPrompt("");
    setFormSuggestOn("");
    setFormColor("#E86C4A");
    setFormError(null);
    setEditingId(null);
  }

  function handleEdit(mode: CustomMode) {
    setFormLabel(mode.label);
    setFormShortLabel(mode.shortLabel);
    setFormDescription(mode.description);
    setFormIcon(mode.icon);
    setFormSystemPrompt(mode.systemPrompt);
    setFormSuggestOn(mode.suggestOn.join(", "));
    setFormColor(mode.color || "#E86C4A");
    setEditingId(mode.id);
    setShowForm(true);
  }

  function handleSave() {
    if (!formLabel.trim()) {
      setFormError("Label is required");
      return;
    }
    if (!formShortLabel.trim()) {
      setFormShortLabel(formLabel.trim());
    }

    const id = editingId || `custom-${Date.now()}`;
    const mode: CustomMode = {
      id,
      label: formLabel.trim(),
      shortLabel: formShortLabel.trim() || formLabel.trim(),
      description: formDescription.trim(),
      icon: formIcon,
      systemPrompt: formSystemPrompt.trim(),
      suggestOn: formSuggestOn
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      color: formColor,
    };

    const existing = loadCustomModes();
    if (editingId) {
      const idx = existing.findIndex((m) => m.id === editingId);
      if (idx >= 0) existing[idx] = mode;
      else existing.push(mode);
    } else {
      existing.push(mode);
    }
    saveCustomModes(existing);
    setCustomModes(existing);
    setShowForm(false);
    resetForm();
  }

  function handleDelete(id: string) {
    const filtered = customModes.filter((m) => m.id !== id);
    saveCustomModes(filtered);
    setCustomModes(filtered);
  }

  function handleDuplicate(mode: CustomMode) {
    const newMode = {
      ...mode,
      id: `custom-${Date.now()}`,
      label: `${mode.label} (Copy)`,
    };
    const existing = loadCustomModes();
    existing.push(newMode);
    saveCustomModes(existing);
    setCustomModes(existing);
  }

  return (
    <div
      className="flex h-full flex-col overflow-y-auto"
      data-testid="modes-screen"
    >
      <div className="mx-auto w-full max-w-3xl px-6 py-8">
        {/* Header */}
        <div className="mb-8 animate-fade-in-up">
          <div className="flex items-center gap-3 mb-4">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="press flex h-8 w-8 items-center justify-center rounded-lg transition-colors hover:opacity-80"
              style={{ color: "var(--text-subtle)" }}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d="M10 4l-4 4 4 4" />
              </svg>
            </button>
            <div>
              <h1
                className="text-xl font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                Modes
              </h1>
              <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
                Create and manage custom agent modes for different workflows
              </p>
            </div>
          </div>
        </div>

        {/* Built-in modes */}
        <section className="mb-8 animate-fade-in-up">
          <h2
            className="text-xs font-semibold uppercase tracking-wider mb-3"
            style={{ color: "var(--text-quiet)" }}
          >
            Built-in Modes
          </h2>
          <div className="flex flex-col gap-2">
            {MODES.filter((m) => m.enabledByDefault).map((mode) => (
              <ModeCard key={mode.id} mode={mode} />
            ))}
          </div>
        </section>

        {/* Custom modes */}
        <section className="mb-8 animate-fade-in-up">
          <div className="flex items-center justify-between mb-3">
            <h2
              className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: "var(--text-quiet)" }}
            >
              Custom Modes {customModes.length > 0 && `(${customModes.length})`}
            </h2>
            <button
              type="button"
              onClick={() => {
                resetForm();
                setShowForm(true);
              }}
              className="press flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
              style={{
                background:
                  "color-mix(in srgb, var(--accent) 10%, transparent)",
                color: "var(--accent)",
                border:
                  "1px solid color-mix(in srgb, var(--accent) 15%, transparent)",
              }}
            >
              <svg
                width="12"
                height="12"
                viewBox="0 0 12 12"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d="M6 2v8M2 6h8" />
              </svg>
              New Mode
            </button>
          </div>

          {customModes.length === 0 && !showForm && (
            <div
              className="flex flex-col items-center gap-3 rounded-xl p-8 text-center"
              style={{
                border: "1px dashed var(--border-strong)",
                background: "var(--surface)",
              }}
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                style={{ color: "var(--text-quiet)" }}
              >
                <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" />
              </svg>
              <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
                No custom modes yet. Create one to extend Wren's capabilities.
              </p>
            </div>
          )}

          <div className="flex flex-col gap-2">
            {customModes.map((mode) => (
              <div
                key={mode.id}
                className="flex items-center gap-3 rounded-xl p-3 card-hover transition-all"
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                }}
              >
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-lg"
                  style={{
                    background: `color-mix(in srgb, ${
                      mode.color || "#E86C4A"
                    } 12%, transparent)`,
                  }}
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke={mode.color || "#E86C4A"}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path
                      d={
                        ICON_OPTIONS.find((o) => o.value === mode.icon)?.svg ||
                        ICON_OPTIONS[0].svg
                      }
                    />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className="text-sm font-medium"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {mode.label}
                    </span>
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded-full"
                      style={{
                        background: `color-mix(in srgb, ${
                          mode.color || "#E86C4A"
                        } 10%, transparent)`,
                        color: mode.color || "#E86C4A",
                      }}
                    >
                      custom
                    </span>
                  </div>
                  <p
                    className="text-xs truncate"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    {mode.description}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleDuplicate(mode)}
                    className="press h-7 w-7 rounded-lg flex items-center justify-center hover:opacity-80"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                    >
                      <rect x="3.5" y="3.5" width="7" height="7" rx="1" />
                      <path d="M8.5 3.5V2a1 1 0 00-1-1H3a1 1 0 00-1 1v4.5a1 1 0 001 1h1.5" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleEdit(mode)}
                    className="press h-7 w-7 rounded-lg flex items-center justify-center hover:opacity-80"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                    >
                      <path d="M8.5 1.5l2 2L4.5 9.5l-2.5.5.5-2.5 5.5-5.5z" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(mode.id)}
                    className="press h-7 w-7 rounded-lg flex items-center justify-center hover:opacity-80"
                    style={{ color: "var(--error)" }}
                  >
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                    >
                      <path d="M2.5 3.5h7M4.5 3.5V2a.5.5 0 01.5-.5h2a.5.5 0 01.5.5v1.5M9.5 3.5v7a.5.5 0 01-.5.5H3a.5.5 0 01-.5-.5v-7" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Create/Edit form */}
        {showForm && (
          <div
            className="animate-fade-in-up card rounded-xl p-6"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
            }}
          >
            <h3
              className="text-sm font-semibold mb-1"
              style={{ color: "var(--text-primary)" }}
            >
              {editingId ? "Edit Mode" : "Create Custom Mode"}
            </h3>
            <p className="text-xs mb-4" style={{ color: "var(--text-subtle)" }}>
              Define keywords, system prompt, and behavior for this mode.
            </p>

            <div className="grid grid-cols-2 gap-4 mb-4">
              {/* Label */}
              <div>
                <label
                  className="block text-xs font-medium mb-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Label *
                </label>
                <input
                  type="text"
                  value={formLabel}
                  onChange={(e) => setFormLabel(e.target.value)}
                  placeholder="e.g. Security Audit"
                  className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
                  style={{
                    background: "var(--claude-canvas)",
                    border: "1px solid var(--border-strong)",
                    color: "var(--text-primary)",
                  }}
                />
              </div>
              {/* Short label */}
              <div>
                <label
                  className="block text-xs font-medium mb-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Short Label
                </label>
                <input
                  type="text"
                  value={formShortLabel}
                  onChange={(e) => setFormShortLabel(e.target.value)}
                  placeholder="e.g. Audit"
                  className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
                  style={{
                    background: "var(--claude-canvas)",
                    border: "1px solid var(--border-strong)",
                    color: "var(--text-primary)",
                  }}
                />
              </div>
            </div>

            {/* Description */}
            <div className="mb-4">
              <label
                className="block text-xs font-medium mb-1"
                style={{ color: "var(--text-secondary)" }}
              >
                Description
              </label>
              <input
                type="text"
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                placeholder="What this mode does..."
                className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
                style={{
                  background: "var(--claude-canvas)",
                  border: "1px solid var(--border-strong)",
                  color: "var(--text-primary)",
                }}
              />
            </div>

            {/* Icon + Color row */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label
                  className="block text-xs font-medium mb-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Icon
                </label>
                <div className="flex gap-1.5 flex-wrap">
                  {ICON_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setFormIcon(opt.value)}
                      className="press flex h-8 w-8 items-center justify-center rounded-lg transition-all"
                      style={{
                        background:
                          formIcon === opt.value
                            ? "color-mix(in srgb, var(--accent) 12%, transparent)"
                            : "var(--claude-canvas)",
                        border:
                          formIcon === opt.value
                            ? "1px solid color-mix(in srgb, var(--accent) 30%, transparent)"
                            : "1px solid var(--border-strong)",
                        color:
                          formIcon === opt.value
                            ? "var(--accent)"
                            : "var(--text-subtle)",
                      }}
                      title={opt.label}
                    >
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d={opt.svg} />
                      </svg>
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label
                  className="block text-xs font-medium mb-1"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Accent Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formColor}
                    onChange={(e) => setFormColor(e.target.value)}
                    className="h-8 w-8 rounded-lg cursor-pointer border-none"
                    style={{ background: "transparent" }}
                  />
                  <span
                    className="text-xs font-mono"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    {formColor}
                  </span>
                </div>
              </div>
            </div>

            {/* Suggest-on keywords */}
            <div className="mb-4">
              <label
                className="block text-xs font-medium mb-1"
                style={{ color: "var(--text-secondary)" }}
              >
                Trigger Keywords{" "}
                <span
                  className="font-normal"
                  style={{ color: "var(--text-quiet)" }}
                >
                  (comma-separated)
                </span>
              </label>
              <input
                type="text"
                value={formSuggestOn}
                onChange={(e) => setFormSuggestOn(e.target.value)}
                placeholder="e.g. security, audit, vuln"
                className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all"
                style={{
                  background: "var(--claude-canvas)",
                  border: "1px solid var(--border-strong)",
                  color: "var(--text-primary)",
                }}
              />
            </div>

            {/* System prompt */}
            <div className="mb-4">
              <label
                className="block text-xs font-medium mb-1"
                style={{ color: "var(--text-secondary)" }}
              >
                System Prompt
              </label>
              <textarea
                value={formSystemPrompt}
                onChange={(e) => setFormSystemPrompt(e.target.value)}
                placeholder="Instructions for the agent in this mode..."
                rows={4}
                className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all resize-y"
                style={{
                  background: "var(--claude-canvas)",
                  border: "1px solid var(--border-strong)",
                  color: "var(--text-primary)",
                  fontFamily: "var(--font-mono)",
                  minHeight: "100px",
                }}
              />
            </div>

            {formError && (
              <p className="text-xs mb-4" style={{ color: "var(--error)" }}>
                {formError}
              </p>
            )}

            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  resetForm();
                }}
                className="press rounded-lg px-4 py-2 text-xs font-medium transition-all"
                style={{
                  color: "var(--text-secondary)",
                  border: "1px solid var(--border)",
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSave}
                className="press rounded-lg px-4 py-2 text-xs font-semibold transition-all"
                style={{
                  background: "var(--accent)",
                  color: "white",
                }}
              >
                {editingId ? "Save Changes" : "Create Mode"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Mode card (built-in) ── */
function ModeCard({ mode }: { mode: ModeDef }) {
  return (
    <div
      className="flex items-center gap-3 rounded-xl p-3 transition-all"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
      }}
    >
      <div
        className="flex h-8 w-8 items-center justify-center rounded-lg"
        style={{
          background: "color-mix(in srgb, var(--accent) 10%, transparent)",
        }}
      >
        {/* Simple icon per mode */}
        <IconForMode icon={mode.icon} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className="text-sm font-medium"
            style={{ color: "var(--text-primary)" }}
          >
            {mode.label}
          </span>
          <span
            className="text-[10px] px-1.5 py-0.5 rounded-full"
            style={{
              background: "color-mix(in srgb, var(--accent) 8%, transparent)",
              color: "var(--accent)",
            }}
          >
            built-in
          </span>
          <div className="flex gap-1">
            {mode.suggestOn.slice(0, 3).map((kw) => (
              <span
                key={kw}
                className="text-[9px] px-1 py-0.5 rounded"
                style={{
                  background:
                    "color-mix(in srgb, var(--accent) 6%, transparent)",
                  color: "var(--text-quiet)",
                }}
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
        <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
          {mode.description}
        </p>
      </div>
    </div>
  );
}

function IconForMode({ icon }: { icon: string }) {
  const size = 14;
  switch (icon) {
    case "clipboard":
      return (
        <svg
          width={size}
          height={size}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
          <rect x="8" y="2" width="8" height="4" rx="1" />
        </svg>
      );
    case "code":
      return (
        <svg
          width={size}
          height={size}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M16 18l6-6-6-6M8 6l-6 6 6 6" />
        </svg>
      );
    case "eye":
      return (
        <svg
          width={size}
          height={size}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      );
    case "bug":
      return (
        <svg
          width={size}
          height={size}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M8 2l4 4 4-4M18 9v1a6 6 0 01-6 6 6 6 0 01-6-6V9" />
          <path d="M6 9H2M22 9h-4M6 15l-3 3M21 18l-3-3M12 16v5M8 21h8" />
        </svg>
      );
    case "help":
      return (
        <svg
          width={size}
          height={size}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      );
    case "video":
      return (
        <svg
          width={size}
          height={size}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <polygon points="23 7 16 12 23 17 23 7" />
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
        </svg>
      );
    default:
      return (
        <svg
          width={size}
          height={size}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="12" cy="12" r="10" />
        </svg>
      );
  }
}
