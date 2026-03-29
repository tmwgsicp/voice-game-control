#!/usr/bin/env python3
# Copyright (C) 2026 VoiceForge Contributors
# Licensed under MIT

"""
Extension lifecycle management.
Extension 生命周期管理（精简版）
"""

import asyncio
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ExtensionState(Enum):
    """Extension 生命周期状态"""
    CREATED = "created"
    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class LifecycleManager:
    """生命周期管理器"""
    
    VALID_TRANSITIONS = {
        ExtensionState.CREATED: [ExtensionState.STARTING],
        ExtensionState.STARTING: [ExtensionState.READY, ExtensionState.ERROR],
        ExtensionState.READY: [ExtensionState.RUNNING, ExtensionState.STOPPING],
        ExtensionState.RUNNING: [ExtensionState.STOPPING],
        ExtensionState.STOPPING: [ExtensionState.STOPPED, ExtensionState.ERROR],
        ExtensionState.STOPPED: [],
        ExtensionState.ERROR: [ExtensionState.STOPPING],
    }
    
    def __init__(self, extension_name: str):
        self.extension_name = extension_name
        self.state = ExtensionState.CREATED
        self._error: Optional[Exception] = None
    
    async def transition_to(self, new_state: ExtensionState):
        """状态转换"""
        old_state = self.state
        
        if not self._is_valid_transition(old_state, new_state):
            raise ValueError(
                f"[{self.extension_name}] 非法的状态转换: {old_state.value} -> {new_state.value}"
            )
        
        self.state = new_state
        logger.info(f"[{self.extension_name}] 状态变化: {old_state.value} -> {new_state.value}")
    
    def _is_valid_transition(self, from_state: ExtensionState, to_state: ExtensionState) -> bool:
        return to_state in self.VALID_TRANSITIONS.get(from_state, [])
    
    def is_ready(self) -> bool:
        return self.state in [ExtensionState.READY, ExtensionState.RUNNING]
    
    def is_running(self) -> bool:
        return self.state == ExtensionState.RUNNING
    
    def is_stopped(self) -> bool:
        return self.state == ExtensionState.STOPPED
    
    def set_error(self, error: Exception):
        self._error = error
        self.state = ExtensionState.ERROR
        logger.error(f"[{self.extension_name}] 进入错误状态: {error}")
