#!/usr/bin/env python3
# Copyright (C) 2026 VoiceForge Contributors
# Licensed under MIT

"""
Extension configuration models.
Extension 配置模型（精简版）
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator


class PortType(Enum):
    """端口数据类型"""
    AUDIO_FRAME = "audio_frame"
    TEXT = "text"
    ANY = "any"


class ExtensionConfig(BaseModel):
    """Extension 基础配置"""
    name: str = Field(..., min_length=1, max_length=100)
    timeout: float = Field(default=30.0, gt=0)
    retry_count: int = Field(default=0, ge=0, le=5)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('名称只能包含字母、数字、下划线和连字符')
        return v


class ASRConfig(ExtensionConfig):
    """ASR Extension 配置"""
    api_key: str = Field(..., description="API Key", min_length=10)
    model: str = Field(default="qwen3-asr-flash-realtime-2026-02-10")
    max_silence_ms: int = Field(default=400, ge=200, le=10000)
    sample_rate: int = Field(default=16000)
    language: str = Field(default="zh")
