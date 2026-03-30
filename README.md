# VoiceGameControl

> **极致低延迟的游戏语音控制工具**  
> 🎮 用语音释放技能，解放双手  
> ⚡ <200ms 响应延迟，专为竞技游戏优化

---

## 💡 项目起源

本项目脱胎于 [VoiceType](https://github.com/tmwgsicp/voicetype) 开源语音输入项目，灵感来源于小红书上看到的 [zhanlong](https://github.com/robotLiberator/zhanlong) 公益项目（语音转键盘输入的无障碍工具）。

VoiceType 的核心设计是**通用语音输入**（ASR + LLM 优化文本），但在游戏场景下发现：
- LLM 处理增加 ~600ms 延迟（游戏不可接受）
- 不需要文本优化，只需要直接触发按键
- 需要极致的响应速度（局内技能释放）

因此，我们将游戏控制功能**独立成专门的项目**，去除 LLM、场景识别等模块，专注于**低延迟语音→按键映射**。

---

## ✨ 核心特性

### ⚡ 极致低延迟
- **Partial 触发**：识别中间结果立即执行（无需等待最终识别）
- **跳过 LLM**：直接映射按键，减少 ~600ms
- **400ms VAD**：快速断句（vs VoiceType 的 1200ms）
- **实测响应**：<200ms（说话 → 按键触发）

### 🎮 游戏优化设计
- **固定场景**：无自动场景识别开销
- **可选声纹**：默认禁用（游戏环境通常单人）
- **灵活映射**：单键、连招、精确/模糊匹配
- **防误触发**：冷却机制（1秒内只触发一次）

### 🔧 功能特性

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

---

## 🔗 相关项目

### VoiceType - 通用语音输入工具
**GitHub**: https://github.com/tmwgsicp/voicetype  
**定位**: 极致轻量的 AI 语音输入（编程、写作、聊天场景）  
**特点**: ASR + LLM 优化、场景自适应、术语规则替换

**技术共享**:
- VoiceGameControl 复用了 VoiceType 的 ASR 框架（VoiceForge）
- 两者共享麦克风采集、热键监听、声纹识别等基础模块
- 但游戏项目去除了 LLM、场景识别等"重"组件

### zhanlong - 无障碍语音输入（灵感来源）
**GitHub**: https://github.com/robotLiberator/zhanlong  
**作者**: 小红书分享的公益项目  
**目标**: 语音转键盘输入，帮助无障碍游戏操作

---

## 🆚 与 VoiceType 的对比

| 特性 | VoiceType | VoiceGameControl |
|-----|-----------|------------------|
| **定位** | 通用语音输入（写代码、文档） | 游戏语音控制 |
| **LLM** | ✅ 润色优化文本 | ❌ 无（直接触发） |
| **场景识别** | ✅ 自动检测应用 | ❌ 固定游戏场景 |
| **声纹验证** | ✅ 默认启用 | ⚠️ 可选（默认禁用） |
| **延迟** | ~1s (含LLM) | <200ms |
| **VAD断句** | 1200ms | 400ms |
| **适用场景** | 编程、写作、聊天 | MOBA、FPS、RPG |

---

## ⚠️ 测试状态

**当前版本**: v0.1.0（开发中）  
**功能状态**: 核心功能已实现，但**尚未经过严格测试**  
**已验证**: 基础语音触发（说"Q"按下q键）  
**待测试**: 连招、冷却、声纹过滤、稳定性

**欢迎体验并反馈问题！** 🙏

---

## 📄 开源协议

**MIT License**

- ✅ 自由使用、修改、分发
- ✅ 商业使用无限制
- ✅ 无需开源修改（vs VoiceType 的 AGPL-3.0）

---

## 🙏 致谢

- [VoiceType](https://github.com/tmwgsicp/voicetype) - 技术框架来源
- [zhanlong](https://github.com/robotLiberator/zhanlong) - 灵感启发（小红书公益项目）
- [Tauri](https://tauri.app/) - 跨平台框架
- [阿里云 DashScope](https://dashscope.aliyun.com/) - ASR 服务
