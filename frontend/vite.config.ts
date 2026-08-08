import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Forward API calls to the local backend so the frontend can use relative
    // /api/* URLs (same as production on Vercel).
    proxy: {
      // 127.0.0.1 (not localhost) to avoid Node resolving to IPv6 ::1 when the
      // backend only listens on IPv4.
      "/api": "http://127.0.0.1:8000",
    },
  },
});
