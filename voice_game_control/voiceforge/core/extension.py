#!/usr/bin/env python3
# Copyright (C) 2026 VoiceForge Contributors
# Licensed under MIT

"""
Extension base class.
Extension 基类（精简版）
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, TypeVar, Union, List

from .config import ExtensionConfig
from .lifecycle import ExtensionState, LifecycleManager

logger = logging.getLogger(__name__)

ConfigT = TypeVar('ConfigT', bound=ExtensionConfig)


class PortType(Enum):
    """端口数据类型"""
    AUDIO_FRAME = "audio_frame"
    TEXT = "text"
    ANY = "any"


@dataclass
class Port:
    """扩展的输入/输出端口"""
    name: str
    port_type: PortType
    description: str = ""
    required: bool = True


@dataclass
class ExtensionMeta:
    """扩展的元数据"""
    name: str
    description: str = ""
    version: str = "0.1.0"
    category: str = "general"


class Extension(ABC, Generic[ConfigT]):
    """可插拔功能模块的基类"""

    metadata: ExtensionMeta = ExtensionMeta(name="base")
    input_ports: List[Port] = []
    output_ports: List[Port] = []
    config_class: type[ConfigT] = ExtensionConfig

    def __init__(self, config: Union[ConfigT, dict[str, Any], None] = None):
        if isinstance(config, dict):
            self.config: ConfigT = self.config_class(**config)
        elif isinstance(config, ExtensionConfig):
            self.config: ConfigT = config
        else:
            self.config: ConfigT = self.config_class(name=self.metadata.name)
        
        self.lifecycle = LifecycleManager(self.config.name)
        self._downstream: dict[str, list[Callable]] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []

    def connect(self, output_port: str, callback: Callable):
        """注册下游回调"""
        self._downstream.setdefault(output_port, []).append(callback)

    async def send(self, port_name: str, data: Any):
        """向指定输出端口发送数据"""
        if not self.lifecycle.is_ready():
            logger.warning(f"[{self.config.name}] Extension 未就绪，无法发送数据")
            return
        
        for cb in self._downstream.get(port_name, []):
            try:
                result = cb(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"[{self.config.name}] 发送数据到端口 {port_name} 失败: {e}")

    async def on_start(self):
        """启动 Extension"""
        await self.lifecycle.transition_to(ExtensionState.STARTING)
        
        try:
            await self._do_start()
            await self.lifecycle.transition_to(ExtensionState.READY)
            await self.lifecycle.transition_to(ExtensionState.RUNNING)
            self._running = True
        except Exception as e:
            self.lifecycle.set_error(e)
            raise

    @abstractmethod
    async def _do_start(self):
        """子类实现具体启动逻辑"""
        pass

    @abstractmethod
    async def on_data(self, port: str, data: Any):
        """接收输入数据"""
        pass

    async def on_stop(self):
        """停止 Extension"""
        if self.lifecycle.is_stopped():
            return
        
        await self.lifecycle.transition_to(ExtensionState.STOPPING)
        
        try:
            self._running = False
            
            for t in self._tasks:
                t.cancel()
            
            if self._tasks:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            
            await self._do_stop()
            
            await self.lifecycle.transition_to(ExtensionState.STOPPED)
        except Exception as e:
            self.lifecycle.set_error(e)
            logger.error(f"[{self.config.name}] 停止时发生错误: {e}")

    async def _do_stop(self):
        """子类实现具体停止逻辑"""
        pass
