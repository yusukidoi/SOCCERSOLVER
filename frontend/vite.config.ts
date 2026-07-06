import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server on 5173; host enabled so it works inside Docker.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
});
