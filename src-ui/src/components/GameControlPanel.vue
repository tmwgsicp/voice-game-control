<!--
 Copyright (C) 2026 VoiceGameControl Contributors
 Licensed under MIT
-->

<template>
  <div class="game-control-panel">
    <el-card class="unified-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">游戏操控模式</span>
          <el-switch
            v-model="gameEnabled"
            @change="handleToggleGameMode"
            active-text="启用"
            inactive-text="禁用"
          />
        </div>
      </template>

      <div class="game-content">
        <div class="intro-section">
          <el-alert type="info" :closable="false" show-icon>
            <template #title>
              按 F9 启动语音识别，说出触发词即可触发按键操作
            </template>
          </el-alert>
          
          <!-- 实时日志 -->
          <div v-if="gameEnabled" class="realtime-log">
            <h4>实时触发日志</h4>
            <div class="log-box">
              <div v-if="recentActions.length === 0" class="log-empty">
                等待语音触发...
              </div>
              <div
                v-for="(log, idx) in recentActions"
                :key="idx"
                class="log-item"
              >
                <span class="log-time">{{ log.time }}</span>
                <span class="log-text">{{ log.text }}</span>
                <span class="log-arrow">→</span>
                <span class="log-action">{{ log.action }}</span>
                <span class="log-keys">{{ log.keys.join(' + ') }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="actions-section">
          <div class="section-header">
            <h3>操作配置</h3>
            <el-button type="primary" @click="handleAddAction" size="default">
              + 添加操作
            </el-button>
          </div>

          <div class="actions-list">
            <el-card
              v-for="action in actions"
              :key="action.name"
              class="action-card"
              shadow="hover"
            >
              <div class="action-header">
                <div class="action-title">
                  <el-switch
                    v-model="action.enabled"
                    @change="handleUpdateAction(action)"
                    size="small"
                  />
                  <span class="action-name">{{ action.name }}</span>
                </div>
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="handleDeleteAction(action.name)"
                >
                  删除
                </el-button>
              </div>

              <div class="action-body">
                <div class="action-row">
                  <span class="label">触发词:</span>
                  <el-tag
                    v-for="(trigger, idx) in action.triggers"
                    :key="idx"
                    size="small"
                    type="primary"
                  >
                    {{ trigger }}
                  </el-tag>
                </div>

                <div class="action-row">
                  <span class="label">按键:</span>
                  <el-tag
                    v-for="(key, idx) in action.keys"
                    :key="idx"
                    size="small"
                    effect="dark"
                  >
                    {{ key }}
                  </el-tag>
                </div>
                
                <div class="action-row">
                  <span class="label">匹配:</span>
                  <el-tag :type="action.exact_match ? 'warning' : 'info'" size="small">
                    {{ action.exact_match ? '精确' : '包含' }}
                  </el-tag>
                </div>

                <div v-if="action.delays && action.delays.length > 0" class="action-row">
                  <span class="label">延迟:</span>
                  <span class="delays-text">{{ action.delays.join('ms, ') }}ms</span>
                </div>
              </div>

              <div class="action-footer">
                <el-button size="small" @click="handleEditAction(action)">
                  编辑
                </el-button>
              </div>
            </el-card>
          </div>

          <el-empty
            v-if="actions.length === 0"
            description="暂无操作配置"
          />
        </div>
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '添加操作' : '编辑操作'"
      width="500px"
    >
      <el-form :model="actionForm" label-width="80px">
        <el-form-item label="操作名称">
          <el-input
            v-model="actionForm.name"
            placeholder="例如: 技能Q"
            :disabled="dialogMode === 'edit'"
          />
        </el-form-item>

        <el-form-item label="触发词">
          <div class="tags-input">
            <el-tag
              v-for="(trigger, idx) in actionForm.triggers"
              :key="idx"
              closable
              @close="actionForm.triggers.splice(idx, 1)"
              size="default"
            >
              {{ trigger }}
            </el-tag>
            <el-input
              v-model="newTrigger"
              size="small"
              placeholder="输入后回车"
              style="width: 120px"
              @keyup.enter="handleAddTrigger"
            />
          </div>
        </el-form-item>

        <el-form-item label="按键序列">
          <div class="tags-input">
            <el-tag
              v-for="(key, idx) in actionForm.keys"
              :key="idx"
              closable
              @close="actionForm.keys.splice(idx, 1)"
              size="default"
              effect="dark"
            >
              {{ key }}
            </el-tag>
            <el-input
              v-model="newKey"
              size="small"
              placeholder="输入后回车"
              style="width: 120px"
              @keyup.enter="handleAddKey"
            />
          </div>
        </el-form-item>

        <el-form-item label="间隔延迟">
          <el-input
            v-model="delaysText"
            placeholder="例如: 50,100（ms）"
          />
        </el-form-item>
        
        <el-form-item label="匹配模式">
          <el-switch
            v-model="actionForm.exact_match"
            active-text="精确匹配"
            inactive-text="包含匹配"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveAction">
          {{ dialogMode === 'add' ? '添加' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useApi } from '../composables/useApi'
import { listen } from '@tauri-apps/api/event'

const { get, post, put, del } = useApi()

const gameEnabled = ref(false)
const actions = ref([])
const recentActions = ref([])
let unlistenGameAction = null

const dialogVisible = ref(false)
const dialogMode = ref('add')
const actionForm = ref({
  name: '',
  triggers: [],
  keys: [],
  delays: [],
  exact_match: false
})
const newTrigger = ref('')
const newKey = ref('')
const delaysText = ref('')

async function loadGameData() {
  try {
    const data = await get('/api/game/actions')
    gameEnabled.value = data.enabled
    actions.value = data.actions || []
    
    if (actions.value.length === 0) {
      ElMessage.warning('没有操作配置')
    }
  } catch (error) {
    ElMessage.error('加载配置失败')
  }
}

async function handleToggleGameMode(enabled) {
  try {
    await post('/api/game/enable', { enabled })
    ElMessage.success(enabled ? '已启用' : '已禁用')
  } catch (error) {
    ElMessage.error('切换失败')
    gameEnabled.value = !enabled
  }
}

function handleAddAction() {
  dialogMode.value = 'add'
  actionForm.value = {
    name: '',
    triggers: [],
    keys: [],
    delays: [],
    exact_match: false
  }
  delaysText.value = ''
  dialogVisible.value = true
}

function handleEditAction(action) {
  dialogMode.value = 'edit'
  actionForm.value = {
    name: action.name,
    triggers: [...action.triggers],
    keys: [...action.keys],
    delays: action.delays ? [...action.delays] : [],
    exact_match: action.exact_match || false
  }
  delaysText.value = action.delays && action.delays.length > 0 
    ? action.delays.join(',') 
    : ''
  dialogVisible.value = true
}

function handleAddTrigger() {
  const trigger = newTrigger.value.trim()
  if (trigger && !actionForm.value.triggers.includes(trigger)) {
    actionForm.value.triggers.push(trigger)
    newTrigger.value = ''
  }
}

function handleAddKey() {
  const key = newKey.value.trim()
  if (key && !actionForm.value.keys.includes(key)) {
    actionForm.value.keys.push(key)
    newKey.value = ''
  }
}

async function handleSaveAction() {
  if (!actionForm.value.name || actionForm.value.triggers.length === 0 || actionForm.value.keys.length === 0) {
    ElMessage.warning('请填写完整信息')
    return
  }

  const delays = delaysText.value
    ? delaysText.value.split(',').map(d => parseInt(d.trim())).filter(d => !isNaN(d))
    : []

  const payload = {
    name: actionForm.value.name,
    triggers: actionForm.value.triggers,
    keys: actionForm.value.keys,
    delays: delays.length > 0 ? delays : undefined,
    exact_match: actionForm.value.exact_match
  }

  try {
    if (dialogMode.value === 'add') {
      await post('/api/game/actions', payload)
      ElMessage.success('已添加')
    } else {
      await put(`/api/game/actions/${actionForm.value.name}`, {
        triggers: payload.triggers,
        keys: payload.keys,
        delays: payload.delays,
        exact_match: payload.exact_match
      })
      ElMessage.success('已更新')
    }
    
    dialogVisible.value = false
    await loadGameData()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

async function handleUpdateAction(action) {
  try {
    await put(`/api/game/actions/${action.name}`, {
      enabled: action.enabled
    })
  } catch (error) {
    ElMessage.error('更新失败')
    action.enabled = !action.enabled
  }
}

async function handleDeleteAction(name) {
  try {
    await del(`/api/game/actions/${name}`)
    ElMessage.success('已删除')
    await loadGameData()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(async () => {
  await loadGameData()
  
  try {
    unlistenGameAction = await listen('backend-event', (event) => {
      const data = event.payload
      if (data.type === 'game_action') {
        const now = new Date()
        const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
        
        recentActions.value.unshift({
          time: timeStr,
          text: data.text,
          action: data.action,
          keys: data.keys
        })
        
        if (recentActions.value.length > 20) {
          recentActions.value.pop()
        }
      }
    })
  } catch (error) {
    console.error('Failed to register listener:', error)
  }
})

onUnmounted(() => {
  if (unlistenGameAction) {
    unlistenGameAction()
  }
})
</script>

<style scoped>
.game-control-panel {
  padding: 0;
}

.unified-card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-large);
  box-shadow: var(--shadow-light);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.game-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.intro-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.actions-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0;
}

.actions-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--space-md);
}

.action-card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-base);
  transition: all var(--duration-normal) var(--ease-in-out);
}

.action-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-base);
}

.action-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.action-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.action-name {
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.action-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.action-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.action-row .label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  min-width: 60px;
}

.delays-text {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.action-footer {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: flex-end;
}

.tags-input {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: center;
  width: 100%;
}

.realtime-log {
  margin-top: var(--space-lg);
  padding: var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-base);
  border: 1px solid var(--border-light);
}

.realtime-log h4 {
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
}

.log-box {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-small);
  padding: var(--space-sm);
  max-height: 200px;
  overflow-y: auto;
}

.log-empty {
  text-align: center;
  color: var(--text-secondary);
  font-size: var(--font-sm);
  padding: var(--space-lg);
}

.log-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) 0;
  border-bottom: 1px solid var(--border-light);
  font-size: var(--font-sm);
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: var(--text-secondary);
  font-family: 'Courier New', monospace;
  min-width: 60px;
}

.log-text {
  color: var(--text-primary);
  font-weight: var(--font-semibold);
  min-width: 60px;
}

.log-arrow {
  color: var(--text-secondary);
}

.log-action {
  color: var(--primary-color);
  font-weight: var(--font-semibold);
}

.log-keys {
  color: var(--text-secondary);
  font-family: 'Courier New', monospace;
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 3px;
}
</style>
