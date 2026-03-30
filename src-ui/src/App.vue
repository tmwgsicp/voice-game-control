<!--
 Copyright (C) 2026 VoiceGameControl Contributors
 Licensed under MIT
-->

<template>
  <div class="game-control-app">
    <div class="header">
      <h1>VoiceGameControl</h1>
      <p class="subtitle">游戏语音控制 - 极致低延迟</p>
    </div>

    <el-tabs v-model="activeTab" class="main-tabs">
      <el-tab-pane label="游戏控制" name="game">
        <GameControlPanel />
      </el-tab-pane>
      
      <el-tab-pane label="声纹管理" name="voiceprint">
        <VoiceprintPanel />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import GameControlPanel from './components/GameControlPanel.vue'
import VoiceprintPanel from './components/VoiceprintPanel.vue'

const activeTab = ref('game')
</script>

<style scoped>
.game-control-app {
  padding: var(--space-lg);
  max-width: var(--width-wide);
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.header h1 {
  font-size: var(--font-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.subtitle {
  font-size: var(--font-base);
  color: var(--text-secondary);
  margin: 0;
}

.main-tabs {
  margin-top: var(--space-lg);
}
</style>
