#!/usr/bin/env python3
# Copyright (C) 2026 VoiceForge Contributors
# Licensed under MIT

"""
Aliyun Qwen3-ASR real-time speech recognition extension.
阿里云Qwen ASR实时语音识别（游戏控制专用版）
"""

import asyncio
import base64
import json
import logging
import uuid
from typing import Any, Optional, Union

import websockets
from websockets.client import WebSocketClientProtocol

from voice_game_control.voiceforge.core.extension import ExtensionMeta, Port, PortType
from voice_game_control.voiceforge.core.config import ASRConfig
from voice_game_control.voiceforge.extensions.base_asr import BaseASRExtension

logger = logging.getLogger(__name__)

QWEN_ASR_WS_BASE = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"


class QwenASRExtension(BaseASRExtension):
    """
    Aliyun Qwen3-ASR real-time speech recognition.
    游戏控制专用版：极致低延迟
    """

    config_class = ASRConfig

    metadata = ExtensionMeta(
        name="qwen_asr",
        description="Aliyun Qwen3-ASR for game control",
        category="asr",
    )
    input_ports = [
        Port("audio_frame", PortType.AUDIO_FRAME, "PCM 16kHz audio frame"),
    ]
    output_ports = [
        Port("text", PortType.TEXT, "Final recognition text"),
        Port("partial_text", PortType.TEXT, "Intermediate recognition result"),
    ]

    def __init__(
        self,
        config: Union[ASRConfig, dict[str, Any], None] = None,
    ):
        super().__init__(config)

        self._api_key: str = self.config.api_key
        self._model: str = self.config.model
        self._max_silence_ms: int = self.config.max_silence_ms
        self._sample_rate: int = self.config.sample_rate
        self._language: str = self.config.language

        self._ws: Optional[WebSocketClientProtocol] = None
        self._session_configured = asyncio.Event()
        self._recv_task: Optional[asyncio.Task] = None
        self._reconnect_lock = asyncio.Lock()

    async def establish_connection(self):
        url = f"{QWEN_ASR_WS_BASE}?model={self._model}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        self._ws = await websockets.connect(
            url,
            additional_headers=headers,
            max_size=None,
        )
        logger.info("[%s] Connected to Qwen ASR: %s", self.config.name, self._model)

        self._recv_task = asyncio.create_task(self._receive_loop())
        self._tasks.append(self._recv_task)

        await self._send_session_update()

        try:
            await asyncio.wait_for(self._session_configured.wait(), timeout=10.0)
            logger.info("[%s] Qwen ASR session configured", self.config.name)
        except asyncio.TimeoutError:
            logger.error("[%s] Qwen ASR session config timeout", self.config.name)
            await self._cleanup_tasks()
            if self._ws:
                await self._ws.close()
            raise ConnectionError("Qwen ASR session config timeout")

    async def _send_session_update(self):
        self._session_configured.clear()

        session_update = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "input_audio_format": "pcm",
                "sample_rate": self._sample_rate,
                "input_audio_transcription": {
                    "language": self._language,
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.0,
                    "silence_duration_ms": self._max_silence_ms,
                },
            },
        }
        await self._ws.send(json.dumps(session_update))
        logger.info(
            "[%s] Sent session.update (VAD mode, silence=%dms, lang=%s)",
            self.config.name, self._max_silence_ms, self._language,
        )

    async def _do_start(self):
        await self.establish_connection()

    async def send_audio(self, audio_data: bytes):
        if not self._ws:
            logger.error("[%s] WebSocket not connected", self.config.name)
            return

        encoded = base64.b64encode(audio_data).decode("ascii")
        event = {
            "event_id": f"audio_{uuid.uuid4().hex[:8]}",
            "type": "input_audio_buffer.append",
            "audio": encoded,
        }

        try:
            await self._ws.send(json.dumps(event))
        except Exception as e:
            logger.error("[%s] Failed to send audio: %s", self.config.name, e)
    
    async def commit_audio(self):
        """
        手动提交音频缓冲区（Manual模式）
        可选功能：进一步降低延迟
        """
        if not self._ws:
            logger.warning("[%s] WebSocket not connected, cannot commit", self.config.name)
            return
        
        event = {
            "event_id": f"commit_{uuid.uuid4().hex[:8]}",
            "type": "input_audio_buffer.commit",
        }
        
        try:
            await self._ws.send(json.dumps(event))
            logger.info("[%s] Manual commit sent", self.config.name)
        except Exception as e:
            logger.error("[%s] Failed to send commit: %s", self.config.name, e)

    async def on_data(self, port: str, data: Any):
        if port == "audio_frame" and isinstance(data, bytes):
            if len(data) == 0:
                return
            await self.send_audio(data)

    async def disconnect(self):
        if self._ws:
            try:
                finish_event = {
                    "event_id": f"fin_{uuid.uuid4().hex[:8]}",
                    "type": "session.finish",
                }
                await self._ws.send(json.dumps(finish_event))
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning("[%s] Error sending session.finish: %s", self.config.name, e)

        await self._cleanup_tasks()

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            logger.info("[%s] Qwen ASR connection closed", self.config.name)

    async def _do_stop(self):
        await self.disconnect()

    async def _cleanup_tasks(self):
        if self._recv_task:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass

    async def _receive_loop(self):
        try:
            async for msg in self._ws:
                if isinstance(msg, bytes):
                    continue

                data = json.loads(msg)
                event_type = data.get("type", "")

                if event_type == "session.created":
                    session_id = data.get("session", {}).get("id", "")
                    logger.info("[%s] Session created: %s", self.config.name, session_id)
                    self._session_configured.set()

                elif event_type == "session.updated":
                    self._session_configured.set()
                    logger.info("[%s] Session configured", self.config.name)

                elif event_type == "conversation.item.input_audio_transcription.text":
                    confirmed_text = data.get("text", "")
                    draft_text = data.get("stash", "")
                    full_text = (confirmed_text + draft_text).strip()
                    
                    if full_text:
                        await self.send("partial_text", full_text)
                        logger.debug("[%s] ASR partial: '%s'", self.config.name, full_text)

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = data.get("transcript", "")
                    if transcript and transcript.strip():
                        await self.send("text", transcript.strip())
                        logger.info("[%s] ASR final: %s", self.config.name, transcript.strip())

                elif event_type == "error":
                    error_msg = data.get("error", {}).get("message", str(data))
                    logger.error("[%s] Qwen ASR error: %s", self.config.name, error_msg)
                    return

            return

        except websockets.exceptions.ConnectionClosed as e:
            logger.error("[%s] WebSocket closed: %s", self.config.name, e)
            await self.send("error", "ASR connection lost")
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error("[%s] Receive loop error: %s", self.config.name, e)
            await self.send("error", f"ASR error: {e}")
