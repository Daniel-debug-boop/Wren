import {
  type RouteConfig,
  layout,
  index,
  route,
} from "@react-router/dev/routes";

export default [
  layout("routes/root-layout.tsx", [
    layout("components/layout/DesktopShell.tsx", [
      index("routes/home.tsx"),
      route("conversations/new", "routes/new-conversation.tsx"),
      route("conversations/:conversationId", "routes/conversation.tsx"),
      route("skills", "routes/skills.tsx"),
      route("settings", "routes/settings.tsx"),
      route("settings/integrations", "routes/settings/integrations.tsx"),
      route("api-keys", "routes/api-keys.tsx"),
      route("video", "routes/video.tsx"),
      route("orchestration", "routes/orchestration.tsx"),
      route("generation", "routes/generation.tsx"),
      route("modes", "routes/modes.tsx"),
    ]),
    route("login", "routes/login.tsx"),
    route("onboarding", "routes/onboarding.tsx"),
    route("oauth/device/verify", "routes/device-verify.tsx"),
    route("redesign", "routes/wren-redesign.tsx"),
  ]),
] satisfies RouteConfig;
