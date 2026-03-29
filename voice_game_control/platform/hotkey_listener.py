#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Global hotkey listener using pynput.
全局快捷键监听器
"""

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

_pynput_GlobalHotKeys = None


class HotkeyListener:
    """全局快捷键监听器"""

    def __init__(self, hotkey: str, on_activate: Callable):
        """
        Args:
            hotkey: 快捷键（pynput格式，如 '<f9>'）
            on_activate: 激活回调函数
        """
        self._hotkey = hotkey
        self._on_activate = on_activate
        self._listener: Optional[any] = None

    def start(self):
        """启动监听"""
        global _pynput_GlobalHotKeys
        if _pynput_GlobalHotKeys is None:
            from pynput.keyboard import GlobalHotKeys
            _pynput_GlobalHotKeys = GlobalHotKeys

        if self._listener:
            logger.warning("Hotkey listener already started")
            return

        hotkeys = {
            self._hotkey: self._on_hotkey_pressed
        }
        
        self._listener = _pynput_GlobalHotKeys(hotkeys)
        self._listener.start()
        
        logger.info(f"HotkeyListener started: {self._hotkey}")

    def stop(self):
        """停止监听"""
        if self._listener:
            self._listener.stop()
            self._listener = None
            logger.info("HotkeyListener stopped")

    def _on_hotkey_pressed(self):
        """快捷键触发回调"""
        logger.info("Voice input activating...")
        try:
            self._on_activate()
        except Exception as e:
            logger.error(f"Hotkey callback error: {e}")
