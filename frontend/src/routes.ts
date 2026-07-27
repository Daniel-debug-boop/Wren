import {
  type RouteConfig,
  layout,
  route,
  index,
} from "@react-router/dev/routes";

export default [
  layout("routes/root-layout.tsx", [
    index("routes/home.tsx"),
    route("settings", "routes/settings.tsx"),
    route("api-keys", "routes/api-keys.tsx"),
    route("generation", "routes/generation.tsx"),
    route("conversation", "routes/conversation.tsx"),
    route("skills", "routes/skills.tsx"),
    route("orchestration", "routes/orchestration.tsx"),
    route("login", "routes/login.tsx"),
  ]),
] satisfies RouteConfig;
