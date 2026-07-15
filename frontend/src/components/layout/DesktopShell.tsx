import { Outlet } from "react-router";
import Sidebar from "./Sidebar";
import WorkspaceFeed from "./WorkspaceFeed";
import ArtifactsDrawer from "./ArtifactsDrawer";
import { ArtifactsProvider } from "./ArtifactsContext";
import { ModeProvider } from "./ModeContext";

export default function DesktopShell() {
  return (
    <div className="flex h-full w-full flex-col overflow-hidden">
      <ModeProvider>
        <ArtifactsProvider>
          <div className="flex flex-1 overflow-hidden animate-fade-in-up">
            {/* Column 1: Sidebar */}
            <Sidebar />

            {/* Column 2: Center Feed */}
            <WorkspaceFeed>
              <Outlet />
            </WorkspaceFeed>

            {/* Column 3: Artifacts Drawer */}
            <ArtifactsDrawer />
          </div>
        </ArtifactsProvider>
      </ModeProvider>
    </div>
  );
}
