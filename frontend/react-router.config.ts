import type { Config } from "@react-router/dev/config";
import { fileURLToPath } from "url";
import path from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * This script is used to unpack the client directory from the frontend build directory.
 * Remix SPA mode builds the client directory into the build directory. This function
 * moves the contents of the client directory to the build directory and then removes the
 * client directory.
 *
 * This script is used in the buildEnd function of the Vite config.
 */
const unpackClientDirectory = async () => {
  const fs = await import("fs");

  const buildDir = path.resolve(__dirname, "build");
  const clientDir = path.resolve(buildDir, "client");

  const files = await fs.promises.readdir(clientDir);
  await Promise.all(
    files.map((file) =>
      fs.promises.rename(
        path.resolve(clientDir, file),
        path.resolve(buildDir, file),
      ),
    ),
  );

  await fs.promises.rmdir(clientDir);
};

export default {
  appDirectory: "src",
  buildEnd: unpackClientDirectory,
  ssr: true,
  // @react-router 8.x enables middleware, the Vite Environment API, and
  // splitRouteModules by default, so the legacy `future.*` flags have been
  // removed. splitRouteModules defaults to `true`.
  splitRouteModules: true,
} satisfies Config;
