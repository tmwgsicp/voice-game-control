#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Voiceprint filter for game audio stream.
游戏音频流的声纹过滤器。
"""

import io
import logging
import wave
from typing import Optional

import numpy as np

from ..platform.voiceprint.base import BaseVoiceprintService

logger = logging.getLogger(__name__)


class VoiceprintFilter:
    """声纹过滤器（游戏优化版）"""
    
    def __init__(
        self,
        service: Optional[BaseVoiceprintService],
        speaker_id: str = "player",
        enabled: bool = False
    ):
        self.service = service
        self.speaker_id = speaker_id
        self.enabled = enabled
        
        self._audio_buffer = []
        self._sample_rate = 16000
        
        logger.info(f"VoiceprintFilter initialized (enabled={enabled}, speaker={speaker_id})")
    
    def set_enabled(self, enabled: bool):
        """动态启用/禁用"""
        self.enabled = enabled
        logger.info(f"Voiceprint filter {'enabled' if enabled else 'disabled'}")
    
    async def verify_audio_chunk(self, audio_pcm: bytes) -> bool:
        """
        验证音频片段是否为本人声音。
        
        Args:
            audio_pcm: PCM 音频数据（16kHz, mono, int16）
        
        Returns:
            True = 通过（本人声音），False = 拒绝（非本人）
        """
        if not self.enabled or not self.service:
            return True
        
        try:
            wav_bytes = self._pcm_to_wav(audio_pcm)
            result = await self.service.verify(self.speaker_id, wav_bytes)
            
            if not result.success:
                logger.warning(f"Voiceprint verify failed: {result.message}")
                return False
            
            if not result.decision:
                logger.info(f"Voiceprint rejected: score={result.score:.1f}")
                return False
            
            logger.debug(f"Voiceprint accepted: score={result.score:.1f}")
            return True
            
        except Exception as e:
            logger.error(f"Voiceprint filter error: {e}")
            return True
    
    def _pcm_to_wav(self, pcm_bytes: bytes) -> bytes:
        """PCM转WAV（内存操作）"""
        pcm_data = np.frombuffer(pcm_bytes, dtype=np.int16)
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self._sample_rate)
            wav.writeframes(pcm_data.tobytes())
        
        return wav_buffer.getvalue()
