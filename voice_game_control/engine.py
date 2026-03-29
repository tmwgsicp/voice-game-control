#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Core engine for game voice control.
游戏语音控制核心引擎（极简版）

特点：
- 无LLM（直接触发按键）
- 无声纹验证（游戏场景不需要）
- 无场景识别（固定游戏场景）
- 极致低延迟（partial触发）
"""

import asyncio
import json
import logging
from typing import Optional, List

from fastapi import WebSocket

from voice_game_control.config import GameControlConfig
from voice_game_control.platform.microphone import Microphone
from voice_game_control.platform.keyboard_output import KeyboardOutput
from voice_game_control.platform.game_action_mapper import GameActionMapper
from voice_game_control.platform.hotkey_listener import HotkeyListener
from voice_game_control.voiceforge.core.config import ASRConfig
from voice_game_control.voiceforge.extensions.providers.aliyun.asr_qwen import QwenASRExtension

logger = logging.getLogger(__name__)


def _task_done_callback(task: asyncio.Task):
    """Task completion callback."""
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Task %s failed: %s", task.get_name(), e)


class GameControlEngine:
    """游戏语音控制引擎"""

    def __init__(
        self,
        asr_api_key: str,
        asr_model: str,
        asr_max_silence_ms: int,
        hotkey: str,
    ):
        self._asr_api_key = asr_api_key
        self._asr_model = asr_model
        self._asr_max_silence_ms = asr_max_silence_ms

        self.game_mapper = GameActionMapper()
        self.keyboard_output = KeyboardOutput()
        
        self.microphone = Microphone()
        self.microphone.on_audio(self._on_audio_chunk)

        self.hotkey_listener = HotkeyListener(
            hotkey=hotkey,
            on_activate=self.start_recording,
        )

        self._recording = False
        self._asr_ext: Optional[QwenASRExtension] = None
        self._ws_clients: List[WebSocket] = []
        
        logger.info("GameControlEngine initialized")

    async def start(self):
        """启动引擎"""
        await self.keyboard_output.start()
        self.hotkey_listener.start()
        logger.info("GameControlEngine started")
        logger.info("Hotkey: %s (toggle recording)", self.hotkey_listener._hotkey)

    async def stop(self):
        """停止引擎"""
        if self._recording:
            await self.stop_recording()
        
        self.hotkey_listener.stop()
        await self.keyboard_output.stop()
        logger.info("GameControlEngine stopped")

    def start_recording(self):
        """启动录音"""
        if self._recording:
            logger.warning("Already recording")
            return

        logger.info("Voice input activating...")
        task = asyncio.create_task(self._start_recording_async(), name="start-recording")
        task.add_done_callback(_task_done_callback)

    async def _start_recording_async(self):
        """异步启动录音"""
        try:
            asr_config = ASRConfig(
                name="game_asr",
                api_key=self._asr_api_key,
                model=self._asr_model,
                max_silence_ms=self._asr_max_silence_ms,
                sample_rate=16000,
                language="zh",
            )

            self._asr_ext = QwenASRExtension(config=asr_config)
            
            self._asr_ext.connect("partial_text", self._on_asr_partial)
            self._asr_ext.connect("text", self._on_asr_final)
            self._asr_ext.connect("error", self._on_asr_error)

            await self._asr_ext.on_start()

            loop = asyncio.get_event_loop()
            self.microphone.start(loop)

            self._recording = True
            
            logger.info("Recording started (mic -> ASR -> game control)")
            await self._broadcast({"type": "recording_started"})

        except Exception as e:
            logger.error("Failed to start recording: %s", e)
            await self._broadcast({"type": "error", "message": str(e)})

    async def stop_recording(self):
        """停止录音"""
        if not self._recording:
            return

        logger.info("Recording stopping...")
        self._recording = False

        self.microphone.stop()
        
        if self._asr_ext:
            await self._asr_ext.on_stop()
            self._asr_ext = None

        logger.info("Recording stopped")
        await self._broadcast({"type": "recording_stopped"})

    async def _on_audio_chunk(self, pcm_data: bytes):
        """麦克风音频回调"""
        if not self._recording or not self._asr_ext:
            return

        try:
            await self._asr_ext.on_data("audio_frame", pcm_data)
        except Exception as e:
            logger.error("Failed to send audio to ASR: %s", e)

    async def _on_asr_partial(self, text: str):
        """ASR partial结果回调（游戏触发核心）"""
        await self._broadcast({"type": "asr_partial", "text": text})
        
        # 游戏模式：立即触发按键
        action = self.game_mapper.match(text)
        if action:
            try:
                if len(action.keys) == 1:
                    await self.keyboard_output.press_key(action.keys[0])
                else:
                    await self.keyboard_output.press_keys_sequence(action.keys, action.delays)
                
                logger.info(f"Game action executed: '{text}' -> {action.name} {action.keys}")
                
                await self._broadcast({
                    "type": "game_action",
                    "text": text,
                    "action": action.name,
                    "keys": action.keys
                })
            except Exception as e:
                logger.error(f"Game action execution failed: {e}")

    async def _on_asr_final(self, text: str):
        """ASR final结果回调"""
        logger.info("ASR final: '%s'", text)
        await self._broadcast({"type": "asr_final", "text": text})

    async def _on_asr_error(self, error_msg: str):
        """ASR错误回调"""
        logger.error("ASR error: %s", error_msg)
        await self._broadcast({"type": "asr_error", "message": str(error_msg)})
        task = asyncio.create_task(self.stop_recording(), name="asr-error-stop")
        task.add_done_callback(_task_done_callback)

    def add_ws_client(self, ws: WebSocket):
        self._ws_clients.append(ws)

    def remove_ws_client(self, ws: WebSocket):
        if ws in self._ws_clients:
            self._ws_clients.remove(ws)

    async def _broadcast(self, data: dict):
        """广播消息到所有WebSocket客户端"""
        if not self._ws_clients:
            return
        message = json.dumps(data, ensure_ascii=False)
        disconnected = []
        for ws in self._ws_clients:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.remove_ws_client(ws)
