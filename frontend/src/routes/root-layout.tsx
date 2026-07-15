import { Outlet } from "react-router";

export default function MainApp() {
  return (
    <div
      data-testid="root-layout"
      className="flex h-full w-full flex-col"
      style={{ background: "var(--claude-canvas)" }}
    >
      <Outlet />
    </div>
  );
}
