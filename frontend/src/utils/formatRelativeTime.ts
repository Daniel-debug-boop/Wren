const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

export function formatRelativeTime(input: Date | string | number): string {
  const date = input instanceof Date ? input : new Date(input);
  const diff = Date.now() - date.getTime();
  if (diff < MINUTE) return "now";
  if (diff < HOUR) return `${Math.floor(diff / MINUTE)}m`;
  if (diff < DAY) return `${Math.floor(diff / HOUR)}h`;
  if (diff < 7 * DAY) return `${Math.floor(diff / DAY)}d`;
  return date.toLocaleDateString(undefined, { weekday: "short" });
}
