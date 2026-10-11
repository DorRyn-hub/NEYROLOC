# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

NEYROLOCK v5 is a PySide6 desktop chat application that connects to multiple LLM backends. Users pick a backend in the sidebar, configure it, select a model, and chat. Responses stream token-by-token via `QThread`.

Three backends only: one local (`Local GGUF`, fully offline via `llama-cpp-python`) and two online (`OpenAI`, `Groq`, under `backends/online/`). LM Studio, Ollama, and HuggingFace GGUF were removed — they duplicated Local GGUF's job with extra moving parts (external server processes for LM Studio/Ollama, a separate download path for HF GGUF that overlapped with `core/model_library.py`).

## Running the app

```bash
# Activate the venv first
source .venv/bin/activate

# Run
python main.py
```

The venv uses Python 3.14 (`.venv/lib/python3.14`). `pip install -r requirements.txt` installs everything except `llama-cpp-python` (Local GGUF) by default.

## Installing the Local GGUF backend

`llama-cpp-python` needs to compile native code, so it's not in `requirements.txt` — install it separately:

```bash
# Apple Silicon (Metal-accelerated)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install "llama-cpp-python>=0.2.0"

# Other platforms
pip install "llama-cpp-python>=0.2.0"
```

## Architecture

```
main.py                       — QApplication entry point, loads APP_QSS stylesheet
ui/main_window.py             — MainWindow: owns Config, ChatSession, active Backend, and two QThreads
ui/sidebar.py                 — Sidebar: backend selector, config form (dynamic), model combo, temperature
ui/chat_widget.py             — ChatWidget: scrollable bubble list + ChatInput (Enter to send)
ui/styles.py                  — APP_QSS: single global stylesheet string
core/config.py                — Config: persists to ~/.neyrolock_5/config.json
core/history.py                — ChatSession + save/load helpers (~/.neyrolock_5/history/)
core/model_library.py         — GGUF download/browse manager shared by Local GGUF + ModelLibraryDialog
core/remote_server.py         — phone remote access: stdlib ThreadingHTTPServer + RemoteBridge (thread-safe Qt bridge)
core/tunnel.py                — public access: manages an `frpc` child process (reverse tunnel to your VPS)
resources/mobile.html         — self-contained mobile web client served by the remote server
ui/remote_dialog.py           — "Удалённый доступ с телефона" dialog: server toggle, pair code, QR (segno)
backends/base.py              — Backend ABC + Message + BackendConfig dataclasses + SAFE_MAX_TOKENS/SAFE_REPEAT_PENALTY
backends/__init__.py          — ALL_BACKENDS = [LocalGGUFBackend, OpenAIBackend, GroqBackend]
backends/local_gguf.py        — Local GGUF backend (llama-cpp-python, offline)
backends/online/              — Cloud backends (OpenAI, Groq), both OpenAI-compatible API via the `openai` SDK
```

## Phone remote access

`Файл → Удалённый доступ с телефона…` starts an HTTP server (port 8765, stdlib only). A phone
on the same Wi-Fi opens `http://<mac-ip>:8765`, enters the 6-digit pair code (persisted in
config as `remote_pair_code`), and gets a mobile chat UI driving the *same* backend the desktop
has connected. Key invariants:

- All state shared with HTTP threads lives in `RemoteBridge` (plain python attrs + Qt signals
  for UI notifications). HTTP handlers must never touch Qt widgets directly.
- `RemoteBridge.generation_lock` serializes generation between desktop (`GenerateWorker`) and
  phone (`/api/chat`) — concurrent generate() calls on one llama.cpp instance crash.
- The phone keeps its own conversation history client-side; the server is stateless
  (`/api/chat` receives the full message list each time, streams plain-text chunks back).
- `/api/chat` accepts optional per-request `system` / `temperature` overrides from the
  phone; they never mutate the desktop's own settings.

## Public access (outside the local Wi-Fi)

`core/tunnel.py` runs `frpc` as a child process, which opens an outbound tunnel to an
`frps` server on your VPS; Caddy there terminates HTTPS and proxies into the tunnel, so
the phone reaches `https://<subdomain>.<domain>` from any network — no port forwarding,
no public IP, no VPN. Settings live under the `tunnel` key in `config.json`
(`server`, `port`, `token`, `subdomain`, `domain`); the toggle is in the remote-access
dialog. The `frpc` binary is looked up in `resources/bin/frpc` first (gitignored — it is
a platform binary). Server-side setup notes: `../remote/README.md`.

## How backends work

Every backend inherits `Backend` (in `backends/base.py`) and must implement:

- `id: str` — unique key used in `config.json`
- `display_name: str` — shown in sidebar
- `config_fields: list[tuple[str, str, str]]` — `(key, label, kind)` where `kind ∈ {"text", "password", "file"}`; drives the dynamic config form in `Sidebar`
- `is_available() -> bool` — returns `True` only if required third-party library is importable
- `list_models() -> list[str]` — called synchronously on the main thread after "Подключить"
- `generate(messages, temperature) -> Iterator[str]` — synchronous generator; runs inside `GenerateWorker(QThread)`
- `prepare(progress)` *(optional)* — heavy setup (model download/load); runs inside `PrepareWorker(QThread)`

To add a new backend: create `backends/my_backend.py` (or `backends/online/my_backend.py` for a cloud API), subclass `Backend`, then add the class to `ALL_BACKENDS` in `backends/__init__.py`. Local/self-hosted backends prone to runaway generation (no reliable EOS) should use `SAFE_MAX_TOKENS`/`SAFE_REPEAT_PENALTY` from `backends/base.py` instead of an unbounded token limit.

## Threading model

`MainWindow` owns two workers:

- **`PrepareWorker`** — calls `backend.prepare()`; emits `progress(str)`, `finishedOk`, `failed(str)`
- **`GenerateWorker`** — iterates `backend.generate()`; emits `chunk(str)`, `finishedOk`, `failed(str)`

Both are plain `QThread` subclasses. Signals cross the thread boundary to update the UI. `GenerateWorker.stop()` sets a flag checked between chunks — backends do not need to be thread-safe or interruptible internally.

## Config & persistence

`Config` auto-saves on every setter call. Keys stored:
- `active_backend` — backend id string
- `temperature` — float
- `system_prompt` — string
- `backends.<id>` — dict of backend-specific config values
- `last_model.<id>` — last selected model per backend

Chat history is saved as JSON files under `~/.neyrolock_5/history/` via `core/history.py`.
