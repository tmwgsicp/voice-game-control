#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""Voiceprint service factory."""

import logging
from typing import Dict, Any

from .base import BaseVoiceprintService, VoiceprintProvider
from .local_service import LocalVoiceprintService

logger = logging.getLogger(__name__)


class VoiceprintServiceFactory:
    """声纹服务工厂"""
    
    @staticmethod
    def create_service(
        provider: VoiceprintProvider,
        config: Dict[str, Any]
    ) -> BaseVoiceprintService:
        """创建声纹服务实例"""
        if provider == VoiceprintProvider.LOCAL_ONNX:
            return LocalVoiceprintService(
                model_path=config["model_path"],
                storage_dir=config["storage_dir"],
                sample_rate=config.get("sample_rate", 16000),
                threshold=config.get("threshold", 0.5)
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
