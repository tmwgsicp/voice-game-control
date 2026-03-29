# VoiceGameControl

游戏语音控制工具 - 极致低延迟的语音按键控制

## 特点

- ⚡ **极致低延迟**：partial触发，跳过LLM，<200ms响应
- 🎮 **专为游戏设计**：无声纹验证、无场景识别、无LLM延迟
- 🔧 **灵活配置**：支持单键、连招、精确/包含匹配
- 🛡️ **防误触发**：冷却机制、精确匹配模式

## 架构

```
VoiceGameControl/
├── voice_game_control/         # Python后端
│   ├── config.py               # 配置管理
│   ├── engine.py               # 核心引擎（无LLM/声纹）
│   ├── main.py                 # FastAPI入口
│   ├── platform/
│   │   ├── game_action_mapper.py  # 操作映射
│   │   ├── keyboard_output.py     # 按键模拟
│   │   ├── microphone.py          # 麦克风采集
│   │   └── hotkey_listener.py     # 全局快捷键
│   ├── voiceforge/             # ASR框架（精简版）
│   │   ├── core/               # 核心基础设施
│   │   └── extensions/         # ASR扩展（仅Aliyun）
│   └── api/
│       └── game_routes.py      # 游戏操作API
└── src-ui/                     # Vue 3 前端
    └── src/
        ├── App.vue             # 主界面
        └── composables/
            └── useApi.ts       # API封装
```

## 快速开始

### 1. 配置环境变量

```bash
export ASR_API_KEY="your_aliyun_api_key"
```

### 2. 安装依赖

```bash
# Python依赖
pip install -r requirements.txt

# 前端依赖
cd src-ui && npm install && cd ..

# Tauri CLI
npm install
```

### 3. 启动开发

```bash
npm run dev
```

### 4. 使用

1. 按 **F9** 启动语音识别
2. 说出触发词（如"Q"、"三连"）
3. 自动触发对应按键操作

## 与 VoiceType 的区别

| 特性 | VoiceType | VoiceGameControl |
|-----|-----------|------------------|
| 定位 | 通用语音输入 | 游戏语音控制 |
| LLM | ✅ 润色文本 | ❌ 无（直接触发） |
| 声纹验证 | ✅ 可选 | ❌ 无 |
| 场景识别 | ✅ 自动切换 | ❌ 无 |
| 延迟 | ~1s | <200ms |
| 复杂度 | 高 | 低 |

## License

MIT
