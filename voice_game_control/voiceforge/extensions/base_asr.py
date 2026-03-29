#!/usr/bin/env python3
# Copyright (C) 2026 VoiceForge Contributors
# Licensed under MIT

"""Base ASR extension class."""

from abc import abstractmethod
from voice_game_control.voiceforge.core.extension import Extension
from voice_game_control.voiceforge.core.config import ASRConfig


class BaseASRExtension(Extension[ASRConfig]):
    """ASR Extension 基类"""

    config_class = ASRConfig

    @abstractmethod
    async def send_audio(self, audio_data: bytes):
        """发送音频数据到ASR"""
        pass
