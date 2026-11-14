import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    // Forward API calls to the FastAPI backend during development
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
});
