#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Voiceprint management API routes for game control.
游戏控制的声纹管理API。
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config import get_config_dir
from ..platform.voiceprint.factory import VoiceprintServiceFactory
from ..platform.voiceprint.base import VoiceprintProvider

logger = logging.getLogger(__name__)

voiceprint_router = APIRouter(prefix="/api/voiceprint", tags=["voiceprint"])

_voiceprint_service = None
_voiceprint_enabled = False
_engine_instance = None


def set_engine_instance(engine):
    """设置Engine实例（由main.py调用）"""
    global _engine_instance
    _engine_instance = engine


def get_voiceprint_service():
    """获取声纹服务实例"""
    global _voiceprint_service
    
    if _voiceprint_service is None:
        config = {
            "model_path": "models/speaker_recognition.onnx",
            "storage_dir": str(get_config_dir() / "voiceprints"),
            "sample_rate": 16000,
            "threshold": 0.6
        }
        _voiceprint_service = VoiceprintServiceFactory.create_service(
            VoiceprintProvider.LOCAL_ONNX,
            config
        )
    
    return _voiceprint_service


class VoiceprintSettings(BaseModel):
    """声纹设置"""
    enabled: bool


class EnrollmentRequest(BaseModel):
    """注册声纹请求"""
    speaker_id: str = Field(..., description="Speaker ID")
    audio_base64: str = Field(..., description="Base64 encoded audio (WAV, 16kHz, mono)")


class ThresholdUpdate(BaseModel):
    """阈值更新"""
    threshold: float = Field(..., ge=0.0, le=1.0)


@voiceprint_router.get("/settings")
async def get_settings():
    """获取声纹设置"""
    return {
        "enabled": _voiceprint_enabled,
        "provider": "local",
        "threshold": 0.6
    }


@voiceprint_router.post("/settings/enable")
async def set_enabled(settings: VoiceprintSettings):
    """启用/禁用声纹识别"""
    global _voiceprint_enabled
    _voiceprint_enabled = settings.enabled
    
    if _engine_instance:
        _engine_instance.set_voiceprint_enabled(_voiceprint_enabled)
    
    logger.info(f"Voiceprint {'enabled' if _voiceprint_enabled else 'disabled'}")
    
    return {"success": True, "enabled": _voiceprint_enabled}


@voiceprint_router.post("/enroll")
async def enroll(req: EnrollmentRequest):
    """注册声纹（支持多轮）"""
    service = get_voiceprint_service()
    
    if not service:
        raise HTTPException(status_code=500, detail="声纹服务未初始化")
    
    try:
        audio_bytes = base64.b64decode(req.audio_base64)
        result = await service.enroll(req.speaker_id, audio_bytes)
        
        if result.success:
            return {
                "success": True,
                "message": result.message,
                "speaker_id": req.speaker_id
            }
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        logger.error(f"Enrollment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@voiceprint_router.get("/list")
async def list_voiceprints():
    """列出所有已注册的声纹"""
    service = get_voiceprint_service()
    
    if not service:
        return {"voiceprints": [], "total": 0}
    
    storage_dir = Path(get_config_dir() / "voiceprints")
    if not storage_dir.exists():
        return {"voiceprints": [], "total": 0}
    
    voiceprints = []
    for vp_file in storage_dir.glob("*.json"):
        try:
            with open(vp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                voiceprints.append({
                    "speaker_id": data["speaker_id"],
                    "threshold": data.get("threshold", 0.6),
                    "provider": "本地 ONNX",
                    "embedding_size": len(data.get("embedding", [])),
                    "enrollment_rounds": data.get("enrollment_rounds", 1),
                    "created_at": vp_file.stat().st_ctime
                })
        except Exception as e:
            logger.error(f"Error reading voiceprint {vp_file}: {e}")
    
    return {
        "voiceprints": voiceprints,
        "total": len(voiceprints),
        "enabled": _voiceprint_enabled
    }


@voiceprint_router.delete("/{speaker_id}")
async def delete_voiceprint(speaker_id: str):
    """删除声纹"""
    service = get_voiceprint_service()
    
    if not service:
        raise HTTPException(status_code=500, detail="声纹服务未初始化")
    
    result = await service.delete(speaker_id)
    
    if result.success:
        return {"success": True, "message": result.message}
    else:
        raise HTTPException(status_code=404, detail=result.message)


@voiceprint_router.put("/{speaker_id}/threshold")
async def update_threshold(speaker_id: str, req: ThresholdUpdate):
    """更新声纹阈值"""
    storage_dir = Path(get_config_dir() / "voiceprints")
    vp_file = storage_dir / f"{speaker_id}.json"
    
    if not vp_file.exists():
        raise HTTPException(status_code=404, detail="声纹不存在")
    
    try:
        with open(vp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data["threshold"] = req.threshold
        
        with open(vp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        return {"success": True, "threshold": req.threshold}
        
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        raise HTTPException(status_code=500, detail=str(e))
