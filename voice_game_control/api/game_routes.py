#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Game Action API Routes
游戏操作API路由
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from voice_game_control.platform.game_action_mapper import GameActionMapper

router = APIRouter(prefix="/api/game", tags=["game"])

_game_mapper: Optional[GameActionMapper] = None


def set_game_mapper(mapper: GameActionMapper):
    """注入GameActionMapper实例"""
    global _game_mapper
    _game_mapper = mapper


class GameActionRequest(BaseModel):
    """游戏操作请求"""
    name: str
    triggers: List[str]
    keys: List[str]
    delays: Optional[List[int]] = None
    exact_match: Optional[bool] = False


class GameActionUpdate(BaseModel):
    """游戏操作更新"""
    triggers: Optional[List[str]] = None
    keys: Optional[List[str]] = None
    delays: Optional[List[int]] = None
    enabled: Optional[bool] = None
    exact_match: Optional[bool] = None


class GameModeStatus(BaseModel):
    """游戏模式状态"""
    enabled: bool


@router.get("/status")
async def get_status():
    """获取游戏模式状态"""
    if not _game_mapper:
        raise HTTPException(status_code=500, detail="Game mapper not initialized")
    
    return {
        "enabled": _game_mapper.enabled,
        "total_actions": len(_game_mapper.actions)
    }


@router.post("/enable")
async def enable_game_mode(status: GameModeStatus):
    """启用/禁用游戏模式"""
    if not _game_mapper:
        raise HTTPException(status_code=500, detail="Game mapper not initialized")
    
    _game_mapper.set_enabled(status.enabled)
    return {"success": True, "enabled": status.enabled}


@router.get("/actions")
async def get_actions():
    """获取所有游戏操作"""
    if not _game_mapper:
        raise HTTPException(status_code=500, detail="Game mapper not initialized")
    
    return {
        "enabled": _game_mapper.enabled,
        "actions": _game_mapper.get_all_actions()
    }


@router.post("/actions")
async def add_action(action: GameActionRequest):
    """添加游戏操作"""
    if not _game_mapper:
        raise HTTPException(status_code=500, detail="Game mapper not initialized")
    
    _game_mapper.add_action(
        name=action.name,
        triggers=action.triggers,
        keys=action.keys,
        delays=action.delays,
        exact_match=action.exact_match or False
    )
    return {"success": True, "message": "Action added"}


@router.put("/actions/{name}")
async def update_action(name: str, update: GameActionUpdate):
    """更新游戏操作"""
    if not _game_mapper:
        raise HTTPException(status_code=500, detail="Game mapper not initialized")
    
    success = _game_mapper.update_action(
        name=name,
        triggers=update.triggers,
        keys=update.keys,
        delays=update.delays,
        enabled=update.enabled,
        exact_match=update.exact_match
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Action not found")
    
    return {"success": True, "message": "Action updated"}


@router.delete("/actions/{name}")
async def delete_action(name: str):
    """删除游戏操作"""
    if not _game_mapper:
        raise HTTPException(status_code=500, detail="Game mapper not initialized")
    
    success = _game_mapper.delete_action(name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Action not found")
    
    return {"success": True, "message": "Action deleted"}
