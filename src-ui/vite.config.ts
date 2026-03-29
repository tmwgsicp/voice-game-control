/**
 * Copyright (C) 2026 VoiceGameControl Contributors
 * Licensed under MIT
 */

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    strictPort: true,
  },
})
