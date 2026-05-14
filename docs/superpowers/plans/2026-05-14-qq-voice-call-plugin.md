# QQ Voice Call Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real AstrBot plugin for QQ voice-call lifecycle handling, Doubao realtime voice-model bridging, and Sylanne memory/emotion summary handoff.

**Architecture:** The plugin separates phone-call transport from model streaming. `napcat_call_adapter.py` exposes a bridge protocol for QQ call invite/accept/audio/hangup events because OneBot v11/NapCat public APIs do not provide a standard telephone audio stream. `doubao_realtime_client.py` is a configurable WebSocket client for Volcengine Doubao realtime voice sessions, while `call_session.py`, `summary.py`, and `sylanne_bridge.py` keep the core behavior testable without real QQ or real Volcengine credentials.

**Tech Stack:** Python 3.10+, AstrBot Star API, WebSocket bridge protocol, Volcengine Doubao realtime voice WebSocket, standard-library unittest.

---

### Task 1: Scaffold plugin identity and packaging

**Files:** `metadata.yaml`, `README.md`, `requirements.txt`, `__init__.py`, `scripts/package_plugin.py`, `scripts/plugin_zip_preflight.js`

- [x] Create AstrBot plugin metadata with `name: astrbot_plugin_qq_voice_call`.
- [x] Document NapCat bridge requirement and Doubao configuration.
- [x] Add package script and zip preflight that enforce the plugin root directory.

### Task 2: Implement testable call core

**Files:** `call_session.py`, `napcat_call_adapter.py`, `doubao_realtime_client.py`, `summary.py`

- [x] Model incoming call events, call state, transcripts, assistant replies, audio frames, and hangup summary.
- [x] Keep NapCat phone transport behind an explicit bridge interface.
- [x] Keep Doubao realtime WebSocket behind a mockable async client interface.

### Task 3: Implement Sylanne bridge

**Files:** `sylanne_bridge.py`, `tests/test_sylanne_bridge.py`

- [x] Discover Sylanne public API helpers when installed.
- [x] Write call summaries via `build_emotion_memory_payload` when available.
- [x] Submit summary text to Sylanne emotion observation when available.
- [x] Return explicit skipped/ok/error status for observability.

### Task 4: AstrBot integration shell

**Files:** `main.py`, `_conf_schema.json`

- [x] Register Star plugin and expose status/help commands.
- [x] Provide bridge event handler methods that tests can call without AstrBot runtime.
- [x] Add safe configuration defaults: no auto-answer unless enabled, bounded call duration, explicit Doubao credentials.

### Task 5: Verification

**Files:** `tests/*.py`

- [x] Unit tests cover call lifecycle, summary generation, Sylanne bridge, config defaults, packaging, and public metadata consistency.
- [x] Run unittest discovery, py_compile, package build, and zip preflight.
