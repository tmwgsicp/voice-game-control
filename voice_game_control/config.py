#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Configuration management for VoiceGameControl.
配置管理（精简版，无LLM/声纹等冗余）
"""

import json
import logging
import os
import sys
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def get_config_dir() -> Path:
    """
    Get persistent config directory.
    获取持久化配置目录。
    """
    if sys.platform == "win32":
        appdata = os.getenv("APPDATA")
        if appdata:
            config_dir = Path(appdata) / "VoiceGameControl"
        else:
            config_dir = Path.home() / "VoiceGameControl"
    elif sys.platform == "darwin":
        config_dir = Path.home() / "Library" / "Application Support" / "VoiceGameControl"
    else:
        config_dir = Path.home() / ".config" / "voice-game-control"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


CONFIG_FILE = get_config_dir() / "config.json"


class GameControlConfig(BaseModel):
    """游戏控制配置（精简版）"""
    
    # ASR配置
    asr_provider: str = Field(default="aliyun", description="ASR provider: aliyun")
    asr_api_key: str = Field(default="", description="ASR API Key")
    asr_model: str = Field(
        default="qwen3-asr-flash-realtime-2026-02-10",
        description="ASR model"
    )
    asr_max_silence_ms: int = Field(
        default=400,
        description="VAD silence threshold (游戏模式建议400ms)"
    )
    
    # 快捷键
    hotkey: str = Field(default="<f9>", description="Toggle hotkey")
    
    # 服务器
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=18234, description="Server port (避免与VoiceType冲突)")
    
    # 自动启动
    auto_start_recording: bool = Field(default=False, description="Auto-start on launch")


def load_config() -> GameControlConfig:
    """Load config with priority: defaults < config.json < .env"""
    config = GameControlConfig()
    
    # 加载 .env 文件
    from pathlib import Path
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())
        except Exception as e:
            logger.warning("Failed to load .env: %s", e)
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_data = json.load(f)
            config = GameControlConfig(**{**config.model_dump(), **file_data})
            logger.info("Loaded config from %s", CONFIG_FILE)
        except Exception as e:
            logger.warning("Failed to load %s: %s", CONFIG_FILE, e)
    
    # 环境变量覆盖
    env_map = {
        "ASR_API_KEY": "asr_api_key",
        "ASR_MODEL": "asr_model",
        "HOTKEY": "hotkey",
        "PORT": "port",
    }
    
    overrides = {}
    for env_key, config_key in env_map.items():
        val = os.getenv(env_key)
        if val is not None:
            field_info = GameControlConfig.model_fields[config_key]
            field_type = field_info.annotation
            
            if field_type == int:
                overrides[config_key] = int(val)
            elif field_type == bool:
                overrides[config_key] = val.lower() in ("true", "1", "yes")
            else:
                overrides[config_key] = val
    
    if overrides:
        config = GameControlConfig(**{**config.model_dump(), **overrides})
    
    return config


def save_config(config: GameControlConfig):
    """Persist config to config.json."""
    data = config.model_dump()
    data.pop("asr_api_key", None)
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Config saved to %s", CONFIG_FILE)
