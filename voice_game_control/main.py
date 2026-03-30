#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

"""
Main entry point for VoiceGameControl.
游戏语音控制主程序
"""

import argparse
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from voice_game_control.config import load_config
from voice_game_control.engine import GameControlEngine
from voice_game_control.api.game_routes import router as game_router, set_game_mapper
from voice_game_control.api.voiceprint_routes import voiceprint_router, set_engine_instance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger(__name__)

engine: GameControlEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    global engine
    
    config = load_config()
    
    if not config.asr_api_key:
        logger.error("ASR_API_KEY not configured!")
        sys.exit(1)
    
    engine = GameControlEngine(
        asr_api_key=config.asr_api_key,
        asr_model=config.asr_model,
        asr_max_silence_ms=config.asr_max_silence_ms,
        hotkey=config.hotkey,
        voiceprint_enabled=config.voiceprint_enabled,
        voiceprint_speaker_id=config.voiceprint_speaker_id,
    )
    
    set_game_mapper(engine.game_mapper)
    set_engine_instance(engine)
    
    await engine.start()
    
    logger.info("=" * 60)
    logger.info("VoiceGameControl service ready")
    logger.info("ASR: %s", config.asr_model)
    logger.info("Voiceprint: %s", "enabled" if config.voiceprint_enabled else "disabled")
    logger.info("Hotkey: %s (toggle recording)", config.hotkey)
    logger.info("Web UI: http://%s:%d/", config.host, config.port)
    logger.info("=" * 60)
    
    yield
    
    await engine.stop()


app = FastAPI(
    title="VoiceGameControl",
    description="游戏语音控制服务",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(voiceprint_router)


@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "recording": engine._recording if engine else False
    }


@app.post("/api/recording/start")
async def start_recording():
    """启动录音"""
    if not engine:
        return {"success": False, "message": "Engine not initialized"}
    
    engine.start_recording()
    return {"success": True}


@app.post("/api/recording/stop")
async def stop_recording():
    """停止录音"""
    if not engine:
        return {"success": False, "message": "Engine not initialized"}
    
    await engine.stop_recording()
    return {"success": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接（前端实时通信）"""
    await websocket.accept()
    
    if engine:
        engine.add_ws_client(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if engine:
            engine.remove_ws_client(websocket)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VoiceGameControl Service")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--tauri", action="store_true", help="Running as Tauri sidecar")
    args = parser.parse_args()
    
    config = load_config()
    port = args.port or config.port
    
    if args.tauri:
        log_prefix = "[python]"
        for handler in logging.root.handlers:
            handler.setFormatter(
                logging.Formatter(f"{log_prefix} %(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
            )
    
    uvicorn.run(
        app,
        host=config.host,
        port=port,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
