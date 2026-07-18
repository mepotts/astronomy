import { defineConfig } from "vite";

// Static SPA. When deploying to GitHub Pages under a project path,
// set base to "/pta-explainer/" (see BUILD-PLAN.md M3). Root "/" is fine for local dev.
export default defineConfig({
  base: "/",
  build: {
    outDir: "dist",
    target: "es2020",
  },
});
