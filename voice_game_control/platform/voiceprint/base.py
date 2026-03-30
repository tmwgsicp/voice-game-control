#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""Base voiceprint service interface."""

from dataclasses import dataclass
from enum import Enum


class VoiceprintProvider(str, Enum):
    """声纹服务提供商"""
    LOCAL_ONNX = "local"


@dataclass
class VoiceprintResult:
    """声纹识别结果"""
    success: bool
    score: float
    decision: bool
    message: str
    provider: str


class BaseVoiceprintService:
    """声纹服务基类"""
    
    def get_provider_name(self) -> str:
        raise NotImplementedError
    
    def is_available(self) -> bool:
        raise NotImplementedError
    
    async def enroll(self, speaker_id: str, audio: bytes, digit: str | None = None) -> VoiceprintResult:
        raise NotImplementedError
    
    async def verify(self, speaker_id: str, audio: bytes, digit: str | None = None) -> VoiceprintResult:
        raise NotImplementedError
    
    async def delete(self, speaker_id: str) -> VoiceprintResult:
        raise NotImplementedError
