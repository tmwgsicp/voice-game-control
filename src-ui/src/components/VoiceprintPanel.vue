<!--
 Copyright (C) 2026 VoiceGameControl Contributors
 Licensed under MIT
-->

<template>
  <div class="voiceprint-panel">
    <!-- Header Card -->
    <section class="unified-card">
      <div class="card-header">
        <div class="header-left">
          <span class="card-title">声纹过滤</span>
          <p class="card-subtitle">仅识别本人声音，降低成本和误触发</p>
        </div>
        <div class="header-right">
          <el-switch
            v-model="enabled"
            @change="toggleEnabled"
            active-text="已启用"
            inactive-text="已禁用"
          />
        </div>
      </div>
    </section>

    <!-- Status Card -->
    <section class="unified-card status-card">
      <div v-if="enabled && voiceprints.length === 0" class="alert alert-warning">
        <span class="alert-icon">⚠</span>
        <div class="alert-content">
          <div class="alert-title">声纹过滤已启用，但未注册声纹</div>
          <div class="alert-text">请先注册声纹才能使用</div>
        </div>
      </div>

      <div v-else-if="enabled && voiceprints.length > 0" class="alert alert-success">
        <span class="alert-icon">✓</span>
        <div class="alert-content">
          <div class="alert-title">声纹过滤运行中</div>
          <div class="alert-text">已注册 {{ voiceprints.length }} 个声纹，自动拦截非本人声音</div>
        </div>
      </div>

      <div v-else class="alert alert-info">
        <span class="alert-icon">ℹ</span>
        <div class="alert-content">
          <div class="alert-title">声纹过滤已禁用</div>
          <div class="alert-text">所有语音都会被识别（更高成本和误触发风险）</div>
        </div>
      </div>
    </section>

    <!-- Voiceprints List -->
    <section class="unified-card">
      <div v-if="voiceprints.length === 0" class="empty-state">
        <div class="empty-icon">🎙</div>
        <div class="empty-title">还没有声纹</div>
        <div class="empty-text">注册声纹后可降低ASR成本并防止误触发</div>
        <el-button type="primary" size="large" @click="showEnrollDialog = true">
          注册声纹
        </el-button>
      </div>

      <div v-else>
        <div class="card-header">
          <span class="card-title">已注册声纹 ({{ voiceprints.length }})</span>
          <el-button type="primary" size="small" @click="showEnrollDialog = true">
            + 注册新声纹
          </el-button>
        </div>

        <div class="voiceprints-list">
          <div
            v-for="vp in voiceprints"
            :key="vp.speaker_id"
            class="voiceprint-item"
          >
            <div class="vp-header">
              <div class="vp-info">
                <span class="vp-icon">🎙</span>
                <div class="vp-details">
                  <div class="vp-name">{{ vp.speaker_id }}</div>
                  <div class="vp-meta">
                    {{ vp.provider }} · {{ vp.embedding_size }} 维向量
                    <span v-if="vp.enrollment_rounds" class="rounds-badge">
                      {{ vp.enrollment_rounds }} 轮
                    </span>
                  </div>
                </div>
              </div>
              <el-button
                type="danger"
                size="small"
                circle
                @click="deleteVoiceprint(vp.speaker_id)"
              >
                ✕
              </el-button>
            </div>

            <div class="vp-body">
              <div class="threshold-control">
                <div class="threshold-header">
                  <label>相似度阈值</label>
                  <span class="threshold-value">{{ vp.threshold.toFixed(2) }}</span>
                </div>
                <el-slider
                  :model-value="vp.threshold"
                  :min="0.5"
                  :max="1.0"
                  :step="0.05"
                  :marks="{ 0.5: '宽松', 0.75: '标准', 1.0: '严格' }"
                  @change="(val: number) => updateThreshold(vp.speaker_id, val)"
                />
                <div class="threshold-hint">
                  较低阈值：易通过但可能误识别 · 较高阈值：严格但可能拒绝本人
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Enrollment Dialog -->
    <el-dialog
      v-model="showEnrollDialog"
      title="注册声纹"
      width="500px"
      :close-on-click-modal="false"
      @close="resetEnrollDialog"
    >
      <!-- Step 0: Input Speaker ID -->
      <div v-if="enrollStep === 0" class="enroll-content">
        <el-form :model="enrollData" label-width="80px">
          <el-form-item label="用户 ID">
            <el-input
              v-model="enrollData.speaker_id"
              placeholder="例如：player"
              maxlength="32"
            />
          </el-form-item>
        </el-form>

        <div class="enroll-guide">
          <div class="guide-title">多轮录音说明</div>
          <ul class="guide-list">
            <li>需要录制 {{ totalRounds }} 轮语音，每轮 3-5 秒</li>
            <li>多轮录入可提高识别准确率</li>
            <li>请在安静环境中清晰朗读提示文字</li>
          </ul>
        </div>
      </div>

      <!-- Step 1: Recording -->
      <div v-if="enrollStep === 1" class="enroll-content">
        <div class="recording-ui">
          <div class="round-indicator">
            第 {{ enrollRound }} / {{ totalRounds }} 轮录音
          </div>
          
          <div class="suggested-text-box">
            <div class="suggested-label">请朗读以下文字：</div>
            <div class="suggested-text">{{ suggestedText }}</div>
          </div>

          <div class="recording-visual">
            <div class="recording-pulse"></div>
            <div class="recording-time">{{ recordingTime }}s / 5s</div>
          </div>

          <div class="recording-hint">
            录音已开始，请清晰朗读上方文字...
          </div>
        </div>
      </div>

      <!-- Step 2: Processing -->
      <div v-if="enrollStep === 2" class="enroll-content">
        <div class="processing-ui">
          <div class="processing-text">正在提取声纹特征...</div>
        </div>
      </div>

      <!-- Step 3: Success -->
      <div v-if="enrollStep === 3" class="enroll-content">
        <div class="success-ui">
          <div class="success-text">声纹注册成功！</div>
        </div>
      </div>

      <template #footer>
        <div v-if="enrollStep === 0">
          <el-button @click="showEnrollDialog = false">取消</el-button>
          <el-button type="primary" @click="startRecording" :disabled="!enrollData.speaker_id.trim()">
            {{ enrollRound === 1 ? '开始录音' : `继续第${enrollRound}轮` }}
          </el-button>
        </div>
        <div v-if="enrollStep === 1">
          <el-button type="danger" @click="stopRecording">停止录音</el-button>
        </div>
        <div v-if="enrollStep === 3">
          <el-button type="primary" @click="resetEnrollDialog">完成</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApi } from '../composables/useApi'

const api = useApi()

const enabled = ref(false)
const voiceprints = ref<any[]>([])
const showEnrollDialog = ref(false)
const enrollStep = ref(0)
const enrollRound = ref(1)
const totalRounds = 3
const isRecording = ref(false)
const recordingTime = ref(0)
const enrollData = ref({ speaker_id: '', audioBlob: null as Blob | null })

const suggestedTexts = [
  '今天天气真不错，我正在测试游戏语音控制。',
  '这是第二轮声纹录入，请保持自然语速。',
  '最后一轮了，感谢您的耐心配合。'
]
const suggestedText = ref(suggestedTexts[0])

let recordingTimer: ReturnType<typeof setInterval> | null = null
let audioContext: AudioContext | null = null
let mediaStream: MediaStream | null = null
let audioProcessor: ScriptProcessorNode | null = null
let audioBuffers: Float32Array[] = []

const toggleEnabled = async () => {
  try {
    await api.post('/api/voiceprint/settings/enable', { enabled: enabled.value })
    ElMessage.success(enabled.value ? '声纹过滤已启用' : '声纹过滤已禁用')
  } catch (error) {
    ElMessage.error('设置失败')
    enabled.value = !enabled.value
  }
}

const loadVoiceprints = async () => {
  try {
    const data = await api.get('/api/voiceprint/list')
    voiceprints.value = data.voiceprints || []
  } catch (error) {
    voiceprints.value = []
    console.error('Failed to load voiceprints:', error)
  }
}

const startRecording = async () => {
  try {
    enrollStep.value = 1
    isRecording.value = true
    recordingTime.value = 0
    audioBuffers = []

    audioContext = new AudioContext({ sampleRate: 16000 })
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const source = audioContext.createMediaStreamSource(mediaStream)
    
    audioProcessor = audioContext.createScriptProcessor(4096, 1, 1)
    
    audioProcessor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0)
      audioBuffers.push(new Float32Array(inputData))
    }

    source.connect(audioProcessor)
    audioProcessor.connect(audioContext.destination)

    recordingTimer = setInterval(() => {
      recordingTime.value++
      if (recordingTime.value >= 5) {
        stopRecording()
      }
    }, 1000)
  } catch (error) {
    ElMessage.error('无法访问麦克风')
    enrollStep.value = 0
  }
}

const stopRecording = () => {
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }

  if (audioProcessor) {
    audioProcessor.disconnect()
    audioProcessor = null
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }

  if (audioContext) {
    audioContext.close()
    audioContext = null
  }

  isRecording.value = false

  if (audioBuffers.length > 0) {
    enrollData.value.audioBlob = createWavBlob(audioBuffers, 16000)
    processEnrollment()
  } else {
    ElMessage.error('录音数据为空')
    enrollStep.value = 0
  }
}

const createWavBlob = (buffers: Float32Array[], sampleRate: number): Blob => {
  const totalLength = buffers.reduce((sum, buf) => sum + buf.length, 0)
  const pcmData = new Int16Array(totalLength)
  let offset = 0
  for (const buf of buffers) {
    for (let i = 0; i < buf.length; i++) {
      pcmData[offset++] = Math.max(-1, Math.min(1, buf[i])) * 0x7FFF
    }
  }

  const wavHeader = new ArrayBuffer(44)
  const view = new DataView(wavHeader)
  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + pcmData.byteLength, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, pcmData.byteLength, true)

  return new Blob([wavHeader, pcmData.buffer], { type: 'audio/wav' })
}

const processEnrollment = async () => {
  enrollStep.value = 2
  try {
    if (!enrollData.value.audioBlob) {
      throw new Error('录音数据为空')
    }
    const audioBuffer = await enrollData.value.audioBlob.arrayBuffer()
    const uint8Array = new Uint8Array(audioBuffer)
    let audio_base64 = ''
    const chunkSize = 8192
    for (let i = 0; i < uint8Array.length; i += chunkSize) {
      const chunk = uint8Array.subarray(i, Math.min(i + chunkSize, uint8Array.length))
      audio_base64 += String.fromCharCode.apply(null, Array.from(chunk))
    }
    audio_base64 = btoa(audio_base64)
    
    const response = await api.post('/api/voiceprint/enroll', {
      speaker_id: enrollData.value.speaker_id,
      audio_base64: audio_base64,
    })
    
    if (enrollRound.value < totalRounds) {
      enrollRound.value++
      suggestedText.value = suggestedTexts[Math.min(enrollRound.value - 1, suggestedTexts.length - 1)]
      ElMessage.success(`第${enrollRound.value - 1}轮完成，继续第${enrollRound.value}轮`)
      enrollStep.value = 0
      recordingTime.value = 0
      audioBuffers = []
    } else {
      enrollStep.value = 3
      await loadVoiceprints()
      ElMessage.success(`声纹注册完成！共${totalRounds}轮`)
    }
  } catch (error: any) {
    const errorMsg = error?.detail || error?.message || '注册失败'
    ElMessage.error(errorMsg)
    showEnrollDialog.value = false
    enrollStep.value = 0
    enrollRound.value = 1
    enrollData.value = { speaker_id: '', audioBlob: null }
  }
}

const resetEnrollDialog = () => {
  showEnrollDialog.value = false
  enrollStep.value = 0
  enrollRound.value = 1
  suggestedText.value = suggestedTexts[0]
  isRecording.value = false
  enrollData.value = { speaker_id: '', audioBlob: null }
  
  if (recordingTimer) {
    clearInterval(recordingTimer)
    recordingTimer = null
  }
}

const updateThreshold = async (speakerId: string, threshold: number) => {
  try {
    await api.put(`/api/voiceprint/${speakerId}/threshold`, { threshold })
    ElMessage.success('阈值已更新')
    await loadVoiceprints()
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

const deleteVoiceprint = async (speakerId: string) => {
  try {
    await ElMessageBox.confirm(`确定删除声纹 "${speakerId}" 吗？`, '确认删除', {
      type: 'warning',
    })
    await api.del(`/api/voiceprint/${speakerId}`)
    ElMessage.success('已删除')
    await loadVoiceprints()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(async () => {
  await loadVoiceprints()
  try {
    const settings = await api.get('/api/voiceprint/settings')
    enabled.value = settings.enabled || false
  } catch (error) {
    console.error('Failed to load voiceprint settings:', error)
  }
})
</script>

<style scoped>
.voiceprint-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.unified-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-large);
  padding: var(--space-lg);
  box-shadow: var(--shadow-light);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  flex: 1;
}

.card-title {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  display: block;
  margin-bottom: var(--space-xs);
}

.card-subtitle {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0;
}

.header-right {
  margin-left: var(--space-lg);
}

.status-card {
  padding: 0;
}

.alert {
  display: flex;
  align-items: flex-start;
  padding: var(--space-md);
  border-radius: var(--radius-base);
}

.alert-warning {
  background: rgba(250, 140, 22, 0.08);
  border-left: 4px solid var(--warning-color);
}

.alert-success {
  background: rgba(82, 196, 26, 0.08);
  border-left: 4px solid var(--success-color);
}

.alert-info {
  background: rgba(24, 144, 255, 0.08);
  border-left: 4px solid var(--primary-color);
}

.alert-icon {
  font-size: 20px;
  margin-right: var(--space-md);
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.alert-text {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.empty-state {
  text-align: center;
  padding: var(--space-xl);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--space-md);
}

.empty-title {
  font-size: var(--font-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.empty-text {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-lg);
}

.voiceprints-list {
  display: grid;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.voiceprint-item {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-base);
  padding: var(--space-md);
  transition: all var(--duration-fast) var(--ease-in-out);
}

.voiceprint-item:hover {
  box-shadow: var(--shadow-light);
}

.vp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.vp-info {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.vp-icon {
  font-size: 24px;
}

.vp-name {
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.vp-meta {
  font-size: var(--font-xs);
  color: var(--text-secondary);
}

.rounds-badge {
  display: inline-block;
  padding: 2px 8px;
  background: var(--primary-color);
  color: white;
  border-radius: var(--radius-small);
  font-size: 11px;
  font-weight: var(--font-semibold);
  margin-left: var(--space-sm);
}

.vp-body {
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-light);
}

.threshold-control {
  padding: var(--space-sm) 0;
}

.threshold-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.threshold-header label {
  font-size: var(--font-sm);
  color: var(--text-primary);
  font-weight: var(--font-semibold);
}

.threshold-value {
  font-size: var(--font-sm);
  color: var(--primary-color);
  font-weight: var(--font-semibold);
}

.threshold-hint {
  font-size: var(--font-xs);
  color: var(--text-secondary);
  margin-top: var(--space-sm);
}

.enroll-content {
  padding: var(--space-lg) 0;
}

.enroll-guide {
  background: var(--bg-secondary);
  padding: var(--space-md);
  border-radius: var(--radius-base);
  margin-top: var(--space-md);
}

.guide-title {
  font-size: var(--font-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}

.guide-list {
  margin: 0;
  padding-left: var(--space-lg);
  font-size: var(--font-sm);
  color: var(--text-secondary);
  line-height: 2;
}

.recording-ui,
.processing-ui,
.success-ui {
  text-align: center;
  padding: var(--space-xl) 0;
}

.round-indicator {
  font-size: var(--font-lg);
  font-weight: var(--font-bold);
  color: var(--primary-color);
  margin-bottom: var(--space-lg);
  padding: var(--space-sm) var(--space-md);
  background: rgba(24, 144, 255, 0.08);
  border-radius: var(--radius-base);
  display: inline-block;
}

.suggested-text-box {
  background: var(--bg-secondary);
  padding: var(--space-md);
  border-radius: var(--radius-base);
  margin-bottom: var(--space-lg);
}

.suggested-label {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.suggested-text {
  font-size: var(--font-base);
  color: var(--text-primary);
  line-height: var(--leading-normal);
  font-weight: var(--font-semibold);
}

.recording-visual {
  margin: var(--space-xl) 0;
}

.recording-pulse {
  width: 80px;
  height: 80px;
  margin: 0 auto var(--space-md);
  background: var(--error-color);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.recording-time {
  font-size: var(--font-xl);
  font-weight: var(--font-bold);
  color: var(--error-color);
}

.recording-hint {
  font-size: var(--font-sm);
  color: var(--text-secondary);
}

.processing-text,
.success-text {
  font-size: var(--font-base);
  color: var(--text-primary);
  margin-top: var(--space-md);
}
</style>
