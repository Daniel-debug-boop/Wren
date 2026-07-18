import { useState } from "react";
import { Outlet } from "react-router";
import Sidebar from "./Sidebar";
import WorkspaceFeed from "./WorkspaceFeed";
import ArtifactsDrawer from "./ArtifactsDrawer";
import { ArtifactsProvider } from "./ArtifactsContext";
import { ModeProvider } from "./ModeContext";
import { AgentStatusProvider, useAgentStatus } from "./AgentStatusContext";
import { TopBar } from "./TopBar";
import { DeployModal } from "./DeployModal";

function ShellInner() {
  const [deployOpen, setDeployOpen] = useState(false);
  const { isRunning, taskCount, elapsedMs } = useAgentStatus();

  return (
    <>
      {/* TopBar */}
      <TopBar
        isRunning={isRunning}
        taskCount={taskCount}
        elapsedMs={elapsedMs}
        onDeploy={() => setDeployOpen(true)}
      />

      {/* 3-column layout */}
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

      {/* Deploy modal */}
      <DeployModal open={deployOpen} onClose={() => setDeployOpen(false)} />
    </>
  );
}

export default function DesktopShell() {
  return (
    <div className="flex h-full w-full flex-col overflow-hidden">
      <ModeProvider>
        <AgentStatusProvider>
          <ArtifactsProvider>
            <ShellInner />
          </ArtifactsProvider>
        </AgentStatusProvider>
      </ModeProvider>
    </div>
  );
}
