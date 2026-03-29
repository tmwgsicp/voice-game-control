#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Game Action Mapper
游戏操作映射器

将语音识别结果直接映射到按键操作，无需LLM介入。
支持单键、组合键、连招配置。
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from voice_game_control.config import get_config_dir

logger = logging.getLogger(__name__)


class GameAction:
    """游戏操作定义"""
    def __init__(
        self,
        name: str,
        triggers: List[str],
        keys: List[str],
        delays: Optional[List[int]] = None,
        enabled: bool = True,
        exact_match: bool = False
    ):
        self.name = name
        self.triggers = triggers
        self.keys = keys
        self.delays = delays or []
        self.enabled = enabled
        self.exact_match = exact_match


class GameActionMapper:
    """游戏操作映射器"""
    
    def __init__(self):
        self.actions: Dict[str, GameAction] = {}
        self.enabled = False
        self._config_file = get_config_dir() / "game_actions.json"
        self._last_trigger_time: Dict[str, float] = {}
        self._trigger_cooldown = 1.0
        self.load()
    
    def load(self):
        """加载游戏操作配置"""
        if not self._config_file.exists():
            self._create_default_config()
            return
        
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.enabled = data.get("enabled", False)
            
            for action_data in data.get("actions", []):
                action = GameAction(
                    name=action_data["name"],
                    triggers=action_data["triggers"],
                    keys=action_data["keys"],
                    delays=action_data.get("delays", []),
                    enabled=action_data.get("enabled", True),
                    exact_match=action_data.get("exact_match", False)
                )
                self.actions[action.name] = action
            
            logger.info(f"Loaded {len(self.actions)} game actions from config")
        
        except Exception as e:
            logger.error(f"Failed to load game actions: {e}")
            self._create_default_config()
    
    def save(self):
        """保存游戏操作配置"""
        data = {
            "enabled": self.enabled,
            "actions": [
                {
                    "name": action.name,
                    "triggers": action.triggers,
                    "keys": action.keys,
                    "delays": action.delays,
                    "enabled": action.enabled,
                    "exact_match": action.exact_match
                }
                for action in self.actions.values()
            ]
        }
        
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Game actions saved")
        except Exception as e:
            logger.error(f"Failed to save game actions: {e}")
    
    def _create_default_config(self):
        """创建默认DOTA配置"""
        default_actions = [
            GameAction("技能Q", ["Q", "q", "Q技能", "q技能", "出Q", "放Q"], ["q"]),
            GameAction("技能W", ["W", "w", "W技能", "w技能", "出W", "放W"], ["w"]),
            GameAction("技能E", ["E", "e", "E技能", "e技能", "出E", "放E"], ["e"]),
            GameAction("大招", ["R", "r", "大招", "大", "开大", "放大"], ["r"]),
            
            GameAction("攻击", ["A", "a", "攻击", "打", "A键"], ["a"]),
            GameAction("停止", ["S", "s", "停止", "停", "S键"], ["s"]),
            
            GameAction("物品1", ["物品1", "物品一", "装备1"], ["z"], exact_match=True),
            GameAction("物品2", ["物品2", "物品二", "装备2"], ["x"], exact_match=True),
            GameAction("物品3", ["物品3", "物品三", "装备3"], ["c"], exact_match=True),
            
            GameAction("跳刀", ["跳刀"], ["space"], exact_match=True),
            
            GameAction("三连", ["三连", "连招", "QWE"], ["q", "w", "e"], delays=[50, 50], enabled=True, exact_match=True),
            GameAction("跳大", ["跳大", "跳刀开大"], ["space", "r"], delays=[120], enabled=True, exact_match=True),
            
            GameAction("测试Q", ["测试Q", "测试Q键"], ["q"], enabled=True),
            GameAction("测试连招", ["测试连招"], ["q", "w", "e"], delays=[200, 200], enabled=True, exact_match=True),
        ]
        
        self.actions = {action.name: action for action in default_actions}
        self.enabled = False
        self.save()
        logger.info("Created default DOTA game actions")
    
    def match(self, text: str) -> Optional[GameAction]:
        """
        匹配语音文本到游戏操作
        
        策略：
        1. 精确匹配优先（完全相等）
        2. 包含匹配次之（触发词在文本中）
        3. 触发冷却检查（1秒内只触发一次）
        """
        if not self.enabled:
            return None
        
        text = text.strip().lower()
        current_time = time.time()
        
        # 第一轮：精确匹配
        for action in self.actions.values():
            if not action.enabled or not action.exact_match:
                continue
            
            for trigger in action.triggers:
                if trigger.lower() == text:
                    last_time = self._last_trigger_time.get(action.name, 0)
                    if current_time - last_time < self._trigger_cooldown:
                        logger.debug(f"Game action in cooldown: {action.name}")
                        return None
                    
                    self._last_trigger_time[action.name] = current_time
                    logger.info(f"Game action matched (exact): '{text}' -> {action.name}")
                    return action
        
        # 第二轮：包含匹配
        for action in self.actions.values():
            if not action.enabled or action.exact_match:
                continue
            
            for trigger in action.triggers:
                trigger_lower = trigger.lower()
                if trigger_lower in text or text in trigger_lower:
                    last_time = self._last_trigger_time.get(action.name, 0)
                    if current_time - last_time < self._trigger_cooldown:
                        logger.debug(f"Game action in cooldown: {action.name}")
                        return None
                    
                    self._last_trigger_time[action.name] = current_time
                    logger.info(f"Game action matched (contains): '{text}' -> {action.name}")
                    return action
        
        return None
    
    def add_action(
        self,
        name: str,
        triggers: List[str],
        keys: List[str],
        delays: Optional[List[int]] = None,
        exact_match: bool = False
    ):
        """添加新的游戏操作"""
        action = GameAction(name, triggers, keys, delays, exact_match=exact_match)
        self.actions[name] = action
        self.save()
    
    def update_action(
        self,
        name: str,
        triggers: Optional[List[str]] = None,
        keys: Optional[List[str]] = None,
        delays: Optional[List[int]] = None,
        enabled: Optional[bool] = None,
        exact_match: Optional[bool] = None
    ):
        """更新游戏操作"""
        if name not in self.actions:
            return False
        
        action = self.actions[name]
        if triggers is not None:
            action.triggers = triggers
        if keys is not None:
            action.keys = keys
        if delays is not None:
            action.delays = delays
        if enabled is not None:
            action.enabled = enabled
        if exact_match is not None:
            action.exact_match = exact_match
        
        self.save()
        return True
    
    def delete_action(self, name: str):
        """删除游戏操作"""
        if name in self.actions:
            del self.actions[name]
            self.save()
            return True
        return False
    
    def set_enabled(self, enabled: bool):
        """启用/禁用游戏模式"""
        self.enabled = enabled
        self.save()
        logger.info(f"Game mode {'ENABLED' if enabled else 'DISABLED'}")
    
    def get_all_actions(self) -> List[Dict[str, Any]]:
        """获取所有游戏操作"""
        return [
            {
                "name": action.name,
                "triggers": action.triggers,
                "keys": action.keys,
                "delays": action.delays,
                "enabled": action.enabled,
                "exact_match": action.exact_match
            }
            for action in self.actions.values()
        ]
