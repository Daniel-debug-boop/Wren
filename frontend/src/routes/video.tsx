import { useMode } from "#/components/layout/ModeContext";

export default function VideoMode() {
  const { mode } = useMode();

  if (mode !== "video") {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2">
        <p className="text-sm text-white/60">
          Switch to <span className="font-medium text-white">Video</span> mode
          in the sidebar to access the video editor.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* ── Header ── */}
      <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold text-white">Video Editor</h1>
          <p className="text-xs text-white/50">
            Remotion-powered mode &mdash; compose and render video in the
            sandbox.
          </p>
        </div>
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/70">
          mode: {mode}
        </span>
      </div>

      {/* ── Content area ── */}
      <div className="flex flex-1 flex-col gap-6 overflow-auto p-6">
        {/* Dependency check */}
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/5 px-4 py-3">
          <span className="text-amber-400 text-sm">⚠</span>
          <p className="text-xs text-amber-300/80">
            Sandbox needs Node 18+, FFmpeg, and @remotion/* installed. Add them
            to the sandbox image before running renders.
          </p>
        </div>

        {/* Getting started guide */}
        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <h2 className="mb-3 text-sm font-medium text-white">
            Getting Started
          </h2>
          <p className="mb-3 text-xs leading-relaxed text-white/50">
            Describe the video you want to create in the chat panel. The agent
            will plan scenes, write Remotion React components, and render the
            result. Start with something simple:
          </p>
          <div className="space-y-2">
            <div className="rounded-md bg-white/5 px-3 py-2 text-xs text-white/60">
              <span className="text-white/40">
                "Create a 10-second animated logo reveal with a dark gradient
                background"
              </span>
            </div>
            <div className="rounded-md bg-white/5 px-3 py-2 text-xs text-white/60">
              <span className="text-white/40">
                "Make a product demo video from these screenshots — 30 seconds,
                with voiceover"
              </span>
            </div>
            <div className="rounded-md bg-white/5 px-3 py-2 text-xs text-white/60">
              <span className="text-white/40">
                "Generate a data-driven chart animation showing Q1 revenue
                growth"
              </span>
            </div>
          </div>
        </div>

        {/* Composition canvas placeholder */}
        <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-white/10 bg-white/5">
          <div className="p-10 text-center">
            <p className="text-sm text-white/60">Composition canvas</p>
            <p className="mt-1 text-xs text-white/40">
              Agent renders Remotion projects here &mdash; output appears in the
              artifacts drawer as .mp4.
            </p>
            <p className="mt-4 text-[10px] text-white/20">
              system prompt: <code>video-editor</code>
            </p>
          </div>
        </div>

        {/* How it works */}
        <details className="group text-xs text-white/40" open>
          <summary className="cursor-pointer font-medium text-white/50 transition hover:text-white/70">
            How this mode works
          </summary>
          <ol className="mt-2 ml-4 list-decimal space-y-1 leading-relaxed">
            <li>
              Agent receives the <code>video-editor</code> system prompt.
            </li>
            <li>
              You describe the video &mdash; topic, style, duration, voice.
            </li>
            <li>
              Agent plans scenes, sources assets, writes Remotion React
              components.
            </li>
            <li>
              Agent renders via <code>npx remotion render</code> or FFmpeg in
              the sandbox.
            </li>
            <li>
              Rendered .mp4 appears in the artifacts drawer for preview or
              download.
            </li>
          </ol>
        </details>

        {/* OpenMontage integration */}
        <details className="group text-xs text-white/40">
          <summary className="cursor-pointer font-medium text-white/50 transition hover:text-white/70">
            OpenMontage integration
          </summary>
          <div className="mt-2 space-y-2 leading-relaxed">
            <p>
              For advanced video workflows, the agent can use{" "}
              <a
                href="https://github.com/danmindru/openmontage"
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/60 underline transition hover:text-white/80"
              >
                OpenMontage
              </a>
              &nbsp;&mdash; a programmatic video composition framework built on
              Remotion.
            </p>
            <ul className="ml-4 list-disc space-y-1">
              <li>
                Pre-built templates for explainers, promos, and data videos
              </li>
              <li>Asset pipeline with automatic sourcing</li>
              <li>Voiceover integration (TTS or recorded)</li>
              <li>Multi-scene storyboarding with transitions</li>
            </ul>
            <p className="text-white/30">
              See the OpenMontage README for template reference and CLI usage.
            </p>
          </div>
        </details>
      </div>
    </div>
  );
}
