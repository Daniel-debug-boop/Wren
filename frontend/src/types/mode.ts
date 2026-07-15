export type ModeId = "plan" | "code" | "review" | "debug" | "ask" | "video" | "game" | "autonomous";

export interface ModeDef {
  id: ModeId;
  label: string;
  shortLabel: string;
  description: string;
  icon: string;
  systemPromptKey: string;
  enabledByDefault: boolean;
  suggestOn: string[];
  autonomous?: boolean; // When true, AI self-routes through plan→code→debug→review cycles
}

export const MODES: ModeDef[] = [
  {
    id: "plan",
    label: "Plan",
    shortLabel: "Plan",
    description: "Read-only analysis — produces structured plan, no file changes",
    icon: "clipboard",
    systemPromptKey: "plan-agent",
    enabledByDefault: true,
    suggestOn: ["refactor", "migrate", "architect", "design", "how"],
    autonomous: false,
  },
  {
    id: "code",
    label: "Code",
    shortLabel: "Code",
    description: "Full agentic coding — reads, edits, runs, tests",
    icon: "code",
    systemPromptKey: "code-agent",
    enabledByDefault: true,
    suggestOn: [],
    autonomous: false,
  },
  {
    id: "review",
    label: "Review",
    shortLabel: "Review",
    description: "Code review — scans diffs, finds bugs, suggests improvements",
    icon: "eye",
    systemPromptKey: "review-agent",
    enabledByDefault: true,
    suggestOn: ["review", "audit", "check", "lint"],
    autonomous: false,
  },
  {
    id: "debug",
    label: "Debug",
    shortLabel: "Debug",
    description: "Root-cause analysis — traces errors, suggests fixes",
    icon: "bug",
    systemPromptKey: "debug-agent",
    enabledByDefault: true,
    suggestOn: ["error", "bug", "crash", "fail", "broken"],
    autonomous: false,
  },
  {
    id: "ask",
    label: "Ask",
    shortLabel: "Ask",
    description: "Q&A about codebase — explains code, finds things",
    icon: "help",
    systemPromptKey: "ask-agent",
    enabledByDefault: true,
    suggestOn: ["what", "where", "how", "why", "explain"],
    autonomous: false,
  },
  {
    id: "video",
    label: "Video",
    shortLabel: "Video",
    description: "Remotion video editor — generates video from prompts",
    icon: "video",
    systemPromptKey: "video-editor",
    enabledByDefault: false,
    suggestOn: ["video", "animation", "motion", "render"],
    autonomous: false,
  },
  {
    id: "game",
    label: "Game",
    shortLabel: "Game",
    description: "Design, prototype, and script a video-game or interactive experience.",
    icon: "gamepad",
    systemPromptKey: "game-agent",
    enabledByDefault: false,
    suggestOn: ["game", "level", "boss", "quest", "character", "rpg", "platformer", "strategy"],
    autonomous: false,
  },
  /* NEW: Autonomous mode flag */
  {
    id: "autonomous",
    label: "Autonomous",
    shortLabel: "Auto",
    description: "Self-driven execution — from plan to completed task without user approval.",
    icon: "robot",
    systemPromptKey: "autonomous-agent",
    enabledByDefault: false,
    suggestOn: ["execute", "finish", "complete", "run it", "do it"],
    autonomous: true,
  },
];

export const DEFAULT_MODE: ModeId = "code";

export function suggestMode(input: string): ModeId | null {
  const lower = input.toLowerCase().trim();
  // Autonomous mode triggers when user says to execute, finish, complete
  if (lower.includes("complete") || lower.includes("execute") || 
     lower.includes("finish") || lower.includes("run") || 
     lower.includes("do it") || lower.includes("launch")) {
    return "autonomous";
  }
  // Regular suggestion logic for all modes
  for (const mode of MODES) {
    if (!mode.enabledByDefault) continue;
    if (mode.suggestOn.some((kw) => lower.startsWith(kw) || lower.includes(` ${kw} `))) {
      return mode.id;
    }
  }
  return null;
}

export function getModeDef(id: ModeId): ModeDef {
  return MODES.find((m) => m.id === id) ?? MODES[1];
}

/* ── Runtime auto-selection from WebSocket events ── */
export type ModeEvent = {
  type: "error" | "action" | "observation";
  actionType?: string;
  content?: string;
};

export function autoSelectMode(event: ModeEvent, currentMode: ModeId): ModeId | null {
  // Never auto-select away from user's manual choice within a turn
  // Only suggest switches when events indicate a different view is needed

  switch (event.type) {
    case "error":
      // Error occurred — switch to debug view
      if (currentMode !== "debug") return "debug";
      return null;

    case "observation": {
      const content = event.content || "";
      // Diff detected — switch to review view
      if (content.includes("diff --git") || content.includes("--- ")) {
        if (currentMode !== "review") return "review";
      }
      return null;
    }

    case "action": {
      // Plan-related action — switch to plan view
      if (event.actionType === "plan" && currentMode !== "plan") return "plan";
      // Running code action — switch to code IDE view
      if (event.actionType === "run" || event.actionType === "edit") {
        if (currentMode !== "code") return "code";
      }
      return null;
    }

    default:
      return null;
  }
}
