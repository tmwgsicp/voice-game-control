#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Local ONNX speaker verification service (lightweight).
本地声纹识别服务（轻量游戏版）
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional
import sherpa_onnx

from .base import BaseVoiceprintService, VoiceprintResult

logger = logging.getLogger(__name__)


class LocalVoiceprintService(BaseVoiceprintService):
    """本地ONNX说话人识别服务（游戏优化版）"""
    
    def __init__(self, model_path: str, storage_dir: str, sample_rate: int = 16000, threshold: float = 0.5):
        self.model_path = Path(model_path)
        self.storage_dir = Path(storage_dir)
        self.sample_rate = sample_rate
        self.threshold = threshold
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(
                model=str(self.model_path),
                num_threads=2,
                debug=False,
                provider="cpu"
            )
            self.extractor = sherpa_onnx.SpeakerEmbeddingExtractor(config)
            logger.info(f"LocalVoiceprintService (game) initialized: {self.model_path.name}")
        except Exception as e:
            logger.error(f"Failed to init speaker extractor: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "本地 ONNX"
    
    def is_available(self) -> bool:
        return self.model_path.exists() and self.extractor is not None
    
    def _voiceprint_file(self, speaker_id: str) -> Path:
        return self.storage_dir / f"{speaker_id}.json"
    
    def _extract_embedding(self, audio: bytes) -> np.ndarray:
        """提取声纹特征向量"""
        try:
            import wave
            import io
            
            with wave.open(io.BytesIO(audio), 'rb') as wav:
                channels = wav.getnchannels()
                rate = wav.getframerate()
                frames = wav.getnframes()
                
                if channels != 1:
                    raise ValueError(f"Expected mono audio, got {channels} channels")
                if rate != self.sample_rate:
                    raise ValueError(f"Expected {self.sample_rate}Hz, got {rate}Hz")
                
                audio_data = wav.readframes(frames)
            
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
        except Exception:
            audio_np = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
        
        stream = self.extractor.create_stream()
        stream.accept_waveform(self.sample_rate, audio_np)
        stream.input_finished()
        
        embedding = self.extractor.compute(stream)
        return np.array(embedding)
    
    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """计算余弦相似度"""
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))
    
    async def enroll(self, speaker_id: str, audio: bytes, digit: Optional[str] = None) -> VoiceprintResult:
        """注册声纹（支持多轮）"""
        try:
            embedding = self._extract_embedding(audio)
            voiceprint_file = self._voiceprint_file(speaker_id)
            
            if voiceprint_file.exists():
                with open(voiceprint_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                existing_embeddings = existing_data.get("embeddings", [])
                if "embedding" in existing_data:
                    existing_embeddings.append(existing_data["embedding"])
                existing_embeddings.append(embedding.tolist())
                avg_embedding = np.mean([np.array(emb) for emb in existing_embeddings], axis=0)
                
                voiceprint_data = {
                    "speaker_id": speaker_id,
                    "embedding": avg_embedding.tolist(),
                    "embeddings": existing_embeddings,
                    "enrollment_rounds": len(existing_embeddings),
                    "threshold": self.threshold
                }
                logger.info(f"Updated voiceprint for {speaker_id} (round {len(existing_embeddings)})")
            else:
                voiceprint_data = {
                    "speaker_id": speaker_id,
                    "embedding": embedding.tolist(),
                    "embeddings": [embedding.tolist()],
                    "enrollment_rounds": 1,
                    "threshold": self.threshold
                }
                logger.info(f"Enrolled voiceprint for {speaker_id} (round 1)")
            
            with open(voiceprint_file, 'w', encoding='utf-8') as f:
                json.dump(voiceprint_data, f)
            
            rounds = voiceprint_data["enrollment_rounds"]
            return VoiceprintResult(
                success=True,
                score=100.0,
                decision=True,
                message=f"注册成功 (第{rounds}轮)",
                provider=self.get_provider_name()
            )
            
        except Exception as e:
            logger.error(f"Enrollment error: {e}")
            return VoiceprintResult(
                success=False,
                score=0.0,
                decision=False,
                message=f"注册失败: {str(e)}",
                provider=self.get_provider_name()
            )
    
    async def verify(self, speaker_id: str, audio: bytes, digit: Optional[str] = None) -> VoiceprintResult:
        """验证声纹（游戏优化：快速拒绝）"""
        try:
            voiceprint_file = self._voiceprint_file(speaker_id)
            
            if not voiceprint_file.exists():
                return VoiceprintResult(
                    success=False,
                    score=0.0,
                    decision=False,
                    message=f"未找到声纹: {speaker_id}",
                    provider=self.get_provider_name()
                )
            
            with open(voiceprint_file, 'r', encoding='utf-8') as f:
                voiceprint_data = json.load(f)
            
            stored_embedding = np.array(voiceprint_data["embedding"])
            threshold = voiceprint_data.get("threshold", self.threshold)
            
            current_embedding = self._extract_embedding(audio)
            similarity = self._cosine_similarity(stored_embedding, current_embedding)
            decision = similarity >= threshold
            
            return VoiceprintResult(
                success=True,
                score=float(similarity * 100),
                decision=decision,
                message=f"相似度: {similarity:.2f}",
                provider=self.get_provider_name()
            )
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return VoiceprintResult(
                success=False,
                score=0.0,
                decision=False,
                message=f"验证失败: {str(e)}",
                provider=self.get_provider_name()
            )
    
    async def delete(self, speaker_id: str) -> VoiceprintResult:
        """删除声纹"""
        try:
            voiceprint_file = self._voiceprint_file(speaker_id)
            
            if voiceprint_file.exists():
                voiceprint_file.unlink()
                logger.info(f"Deleted voiceprint for {speaker_id}")
                message = "删除成功"
            else:
                message = f"声纹不存在: {speaker_id}"
            
            return VoiceprintResult(
                success=True,
                score=0.0,
                decision=True,
                message=message,
                provider=self.get_provider_name()
            )
            
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return VoiceprintResult(
                success=False,
                score=0.0,
                decision=False,
                message=f"删除失败: {str(e)}",
                provider=self.get_provider_name()
            )
