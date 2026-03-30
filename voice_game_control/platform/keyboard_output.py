#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Keyboard output for game control.
键盘输出模块（游戏控制专用版）
"""

import asyncio
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

_pynput_controller = None
_pynput_Key = None


def _ensure_pynput():
    global _pynput_controller, _pynput_Key
    if _pynput_controller is None:
        from pynput.keyboard import Controller, Key
        _pynput_controller = Controller()
        _pynput_Key = Key


class KeyboardOutput:
    """游戏按键输出（直接按键，无剪贴板）"""

    def __init__(self):
        pass

    async def start(self):
        _ensure_pynput()
        logger.info("KeyboardOutput initialized (mode=direct-press)")

    async def stop(self):
        pass
    
    async def press_key(self, key: str):
        """
        直接按下单个按键（游戏优化：同步执行）
        
        Args:
            key: 按键名称（如 'q', 'space', 'ctrl'）
        """
        _ensure_pynput()
        
        try:
            key_obj = self._map_key(key)
            _pynput_controller.press(key_obj)
            _pynput_controller.release(key_obj)
            logger.debug(f"Pressed key: {key}")
        except Exception as e:
            logger.error(f"Failed to press key '{key}': {e}")
    
    async def press_keys_sequence(self, keys: List[str], delays: Optional[List[int]] = None):
        """
        执行按键序列（游戏优化：同步执行连招）
        
        Args:
            keys: 按键列表（如 ['q', 'w', 'e']）
            delays: 按键间延迟（ms）
        """
        import time
        
        _ensure_pynput()
        delays = delays or []
        
        try:
            for i, key in enumerate(keys):
                key_obj = self._map_key(key)
                _pynput_controller.press(key_obj)
                _pynput_controller.release(key_obj)
                
                if i < len(keys) - 1:
                    delay_ms = delays[i] if i < len(delays) else 50
                    time.sleep(delay_ms / 1000.0)
                    
            logger.info(f"Executed key sequence: {keys}")
        except Exception as e:
            logger.error(f"Failed to execute key sequence: {e}")
    
    def _map_key(self, key_name: str):
        """映射按键名称到pynput Key对象"""
        _ensure_pynput()
        
        special_keys = {
            'space': _pynput_Key.space,
            'enter': _pynput_Key.enter,
            'tab': _pynput_Key.tab,
            'esc': _pynput_Key.esc,
            'escape': _pynput_Key.esc,
            'backspace': _pynput_Key.backspace,
            'delete': _pynput_Key.delete,
            'up': _pynput_Key.up,
            'down': _pynput_Key.down,
            'left': _pynput_Key.left,
            'right': _pynput_Key.right,
            'shift': _pynput_Key.shift,
            'ctrl': _pynput_Key.ctrl,
            'alt': _pynput_Key.alt,
            'cmd': _pynput_Key.cmd,
            'caps_lock': _pynput_Key.caps_lock,
            'home': _pynput_Key.home,
            'end': _pynput_Key.end,
            'page_up': _pynput_Key.page_up,
            'page_down': _pynput_Key.page_down,
        }
        
        for i in range(1, 13):
            special_keys[f'f{i}'] = getattr(_pynput_Key, f'f{i}')
        
        key_lower = key_name.lower()
        
        if key_lower in special_keys:
            return special_keys[key_lower]
        else:
            return key_name.lower()
