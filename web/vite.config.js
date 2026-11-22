import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
const api = { "/api": { target: "http://localhost:8000", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") } };
export default defineConfig({ plugins: [react()], server: { port: 5173, proxy: api }, preview: { proxy: api } });
