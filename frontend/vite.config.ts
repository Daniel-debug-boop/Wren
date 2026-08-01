import { defineConfig } from "vite";
import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [reactRouter(), tailwindcss(), tsconfigPaths()],
  server: {
    host: "0.0.0.0",
    port: parseInt(process.env.PORT || "5173"),
    hmr: false,
  },
  build: {
    sourcemap: false,
  },
});
