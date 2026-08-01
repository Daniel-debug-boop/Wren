export const SETTINGS_QUERY_KEYS = {
  all: ["settings"] as const,
  detail: (id: string) => ["settings", id] as const,
};

export default SETTINGS_QUERY_KEYS;
