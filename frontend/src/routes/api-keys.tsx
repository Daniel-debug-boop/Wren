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
    <div className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            API Keys
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-tertiary)" }}>
            Manage API keys for accessing Wren's API programmatically.
          </p>
        </div>
        <button
          onClick={() => setShowNew(!showNew)}
          className="accent-button text-xs"
        >
          {showNew ? "Cancel" : "+ New Key"}
        </button>
      </div>

      {/* Create new key */}
      {showNew && (            <div className="card p-6 mb-6">
              <h2 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>
                Create New API Key
              </h2>
          <div className="flex gap-2">
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
              className="accent-button text-xs"
            >
              {createMutation.isPending ? "Creating..." : "Create"}
            </button>
          </div>
        </div>
      )}

      {/* Keys list */}
      <div className="card">
        {keys.length === 0 ? (
          <div className="p-12 text-center">
            <div className="mb-3 text-2xl">🔑</div>
            <p className="text-sm font-medium mb-1" style={{ color: "var(--text-secondary)" }}>
              No API keys yet
            </p>
            <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Create your first key to start using the Wren API.
            </p>
          </div>
        ) : (
          <div className="divide-y" style={{ borderColor: "var(--border)" }}>
            {keys.map((key: any) => (
              <div
                key={key.id}
                className="flex items-center justify-between px-6 py-4"
              >
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {key.name}
                  </p>
                  <div className="mt-1 flex items-center gap-2">
                    <code className="rounded bg-white/5 px-2 py-0.5 text-xs font-mono" style={{ color: "var(--text-tertiary)" }}>
                      {key.key_preview}...
                    </code>
                    <span className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>
                      Created {key.created_at ? new Date(key.created_at).toLocaleDateString() : ""}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(key.id)}
                  className="rounded-lg px-3 py-1.5 text-xs text-red-400 transition-colors hover:bg-red-500/10"
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
