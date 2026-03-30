#!/usr/bin/env python3
# Copyright (C) 2026 VoiceGameControl Contributors
# Licensed under MIT

from setuptools import setup, find_packages

setup(
    name="voice-game-control",
    version="0.1.0",
    description="Low-latency voice control for games",
    author="VoiceGameControl Contributors",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.32.0",
        "websockets>=14.1",
        "pydantic>=2.10.0",
        "pynput>=1.7.7",
        "sounddevice>=0.5.1",
        "numpy>=2.0.0",
        "sherpa-onnx>=1.10.0",
    ],
    entry_points={
        "console_scripts": [
            "voice-game-control=voice_game_control.main:main",
        ],
    },
)
