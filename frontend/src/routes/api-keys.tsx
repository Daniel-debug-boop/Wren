"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiKeysApi } from "#/api/endpoints";

/* ── API Keys Page ───────────────────────────────────────────────────────────
 * Full API key management: list existing keys, create new ones, delete.
 * Shows key previews and creation dates.
 */

export default function ApiKeysPage() {
  const [keyName, setKeyName] = useState("");
  const [showNew, setShowNew] = useState(false);

  const { data: keys = [], refetch } = useQuery({
    queryKey: ["api-keys"],
    queryFn: () => apiKeysApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => apiKeysApi.create(name),
    onSuccess: () => {
      setKeyName("");
      setShowNew(false);
      refetch();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiKeysApi.delete(id),
    onSuccess: () => refetch(),
  });

  return (
    <div className="mx-auto max-w-4xl animate-fade-up px-4 py-8 md:px-6 md:py-12">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1
            className="font-display text-xl font-semibold tracking-tight md:text-2xl"
            style={{ color: "var(--text-primary)" }}
          >
            API Keys
          </h1>
          <p
            className="mt-1.5 text-sm leading-relaxed"
            style={{ color: "var(--text-tertiary)" }}
          >
            Manage API keys for accessing Wren's API programmatically.
          </p>
        </div>
        <button
          onClick={() => setShowNew(!showNew)}
          className="accent-button shrink-0 text-xs"
        >
          {showNew ? "Cancel" : "+ New Key"}
        </button>
      </div>

      {/* Create new key */}
      {showNew && (
        <div className="card animate-fade-in mb-6 p-5 md:p-6">
          <h2
            className="font-display mb-4 text-sm font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            Create New API Key
          </h2>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              className="input flex-1"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="e.g., Production CI Key"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") createMutation.mutate(keyName);
                if (e.key === "Escape") setShowNew(false);
              }}
            />
            <button
              onClick={() => createMutation.mutate(keyName)}
              disabled={!keyName.trim() || createMutation.isPending}
              className="accent-button shrink-0 text-xs"
            >
              {createMutation.isPending ? "Creating..." : "Create"}
            </button>
          </div>
        </div>
      )}

      {/* Keys list */}
      <div className="card overflow-hidden">
        {keys.length === 0 ? (
          <div className="animate-fade-up p-12 text-center">
            <div
              className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-2xl"
              style={{
                background: "var(--accent-subtle)",
                color: "var(--accent-strong)",
              }}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
              </svg>
            </div>
            <p
              className="mb-1 font-display text-[15px] font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              No API keys yet
            </p>
            <p
              className="text-xs leading-relaxed"
              style={{ color: "var(--text-tertiary)" }}
            >
              Create your first key to start using the Wren API.
            </p>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: "var(--border)" }}>
            {keys.map((key: any) => (
              <div
                key={key.id}
                className="flex flex-col gap-3 px-5 py-4 transition-colors duration-150 hover:bg-black/[0.02] sm:flex-row sm:items-center sm:justify-between md:px-6"
              >
                <div className="min-w-0">
                  <p
                    className="text-sm font-medium"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {key.name}
                  </p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    <code
                      className="rounded-md px-2 py-0.5 font-mono text-xs"
                      style={{
                        background: "var(--bg-surface)",
                        color: "var(--accent-strong)",
                      }}
                    >
                      {key.key_preview}...
                    </code>
                    <span
                      className="text-[10px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      Created{" "}
                      {key.created_at
                        ? new Date(key.created_at).toLocaleDateString()
                        : ""}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(key.id)}
                  className="shrink-0 self-start rounded-lg border border-transparent px-3 py-1.5 text-xs font-medium transition-all duration-150 hover:border-[rgba(191,66,64,0.25)]"
                  style={{ color: "var(--status-error)" }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(191,66,64,0.07)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                  }}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
