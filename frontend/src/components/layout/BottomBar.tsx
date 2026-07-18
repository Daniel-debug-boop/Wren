import { Terminal } from "../Terminal";

export function BottomBar() {
  return (
    <div className="h-full w-full" style={{ background: 'var(--bg)' }}>
      <Terminal />
    </div>
  );
}
