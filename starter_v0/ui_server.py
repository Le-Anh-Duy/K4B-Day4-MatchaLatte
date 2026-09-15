from __future__ import annotations

import argparse
import json
import os
import re
import threading
import uuid
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from chat import now_iso, run_model_tool_loop, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "ui"
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

PROVIDER_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def detect_provider(explicit_provider: str | None) -> str:
    if explicit_provider:
        return explicit_provider
    for provider_name, env_name in PROVIDER_KEYS.items():
        if os.getenv(env_name):
            return provider_name
    return "demo"


def normalize_assistant_text(result: dict[str, Any]) -> None:
    """Show a structured response's reply field while preserving its raw value."""
    raw_text = result.get("assistant_text")
    if not isinstance(raw_text, str):
        return
    candidate = raw_text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return
    if isinstance(payload, dict) and isinstance(payload.get("reply"), str):
        result["raw_assistant_text"] = raw_text
        result["assistant_text"] = payload["reply"]


class HelpdeskWebApp:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.system_prompt = args.system_prompt.read_text(encoding="utf-8")
        self.tools = to_openai_tools(load_tool_declarations(args.tools))
        self.provider = make_provider(args.provider)
        self.model = args.model or getattr(self.provider, "default_model", None)
        self.artifact_version = build_artifact_version(args.version, args.system_prompt, args.tools)
        self.sessions: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def metadata(self) -> dict[str, Any]:
        return {
            **artifact_version_dict(self.artifact_version),
            "provider": self.args.provider,
            "model": self.model,
            "max_tool_rounds": self.args.max_tool_rounds,
        }

    def _new_session(self) -> dict[str, Any]:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_id = f"ui_{self.args.version}_{self.args.provider}_{timestamp}"
        return {
            "history": [],
            "transcript_path": self.args.transcripts_dir / f"{transcript_id}.transcript.json",
            "transcript": {
                "transcript_id": transcript_id,
                "source": "web_ui",
                **self.metadata(),
                "system_prompt": str(self.args.system_prompt),
                "tools": str(self.args.tools),
                "history_window": self.args.history_window,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "turns": [],
            },
        }

    def chat(self, session_id: str, user_text: str) -> dict[str, Any]:
        with self.lock:
            session = self.sessions.get(session_id)
            if session is None:
                session = self._new_session()
                self.sessions[session_id] = session
            history = list(session["history"])
            turn_index = len(session["transcript"]["turns"]) + 1

            if user_text.lower() in {"/exit", "/quit"}:
                ended_at = now_iso()
                session["transcript"].update({"status": "closed", "ended_at": ended_at})
                write_transcript(session["transcript_path"], session["transcript"])
                return {
                    "session_id": session_id,
                    "status": "session_ended",
                    "assistant_text": "Phiên chat đã kết thúc và transcript đã được lưu.",
                    "tool_events": [],
                    "ended_at": ended_at,
                    "artifact_version": self.artifact_version.artifact_version,
                }

        turn: dict[str, Any] = {
            "turn_index": turn_index,
            "started_at": now_iso(),
            "user": user_text,
            "status": "started",
            "assistant_text": None,
            "rounds": [],
            "tool_events": [],
        }
        messages = [
            {"role": "system", "content": self.system_prompt},
            *trim_history(history, self.args.history_window),
            {"role": "user", "content": user_text},
        ]
        try:
            result = run_model_tool_loop(
                provider=self.provider, messages=messages, tools=self.tools,
                model=self.args.model, max_tool_rounds=self.args.max_tool_rounds,
            )
            normalize_assistant_text(result)
            turn.update(result)
            assistant_text = result["assistant_text"]
            with self.lock:
                session["history"].extend([
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": assistant_text},
                ])
        except Exception as exc:
            error_text = f"{type(exc).__name__}: {exc}"
            turn.update({
                "status": "provider_error",
                "assistant_text": "Gemini không thể xử lý yêu cầu. Không có phản hồi dự phòng được tạo.",
                "error": error_text,
            })

        turn["ended_at"] = now_iso()
        with self.lock:
            session["transcript"]["turns"].append(turn)
            write_transcript(session["transcript_path"], session["transcript"])
        return {**turn, "session_id": session_id, "artifact_version": self.artifact_version.artifact_version}


def make_handler(app: HelpdeskWebApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _static(self, filename: str, content_type: str) -> None:
            path = STATIC_DIR / filename
            if not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            body = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            assets = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/index.html": ("index.html", "text/html; charset=utf-8"),
                "/styles.css": ("styles.css", "text/css; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            }
            if path in assets:
                self._static(*assets[path])
            elif path == "/api/meta":
                self._json(app.metadata())
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            if urlparse(self.path).path != "/api/chat":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length) or b"{}")
                message = str(data.get("message", "")).strip()
                if not message:
                    self._json({"error": "message_required"}, HTTPStatus.BAD_REQUEST)
                    return
                session_id = str(data.get("session_id") or uuid.uuid4().hex)
                self._json(app.chat(session_id, message))
            except (ValueError, json.JSONDecodeError):
                self._json({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            print(f"[ui] {self.address_string()} - {format % args}")

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Light-theme web UI for the IT Helpdesk Agent.")
    parser.add_argument("--provider", choices=["demo", "openrouter", "openai", "anthropic", "gemini"], default=None,
                        help="Auto-detected from .env when omitted.")
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", default="v3", help="Artifact version label (default: v3).")
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("--transcripts-dir", type=Path, default=ROOT / "transcripts")
    parser.add_argument("--history-window", type=int, default=5)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8011,
                        help="HTTP port (default: 8011, separate from older UI processes).")
    parser.add_argument("--open-browser", action="store_true", help="Open the UI after the server starts.")
    args = parser.parse_args()
    args.provider = detect_provider(args.provider)

    app = HelpdeskWebApp(args)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    print(f"IT Helpdesk UI: http://{args.host}:{args.port}")
    print(f"artifact_version={app.artifact_version.artifact_version}")
    if args.open_browser:
        threading.Timer(0.5, webbrowser.open, args=(f"http://{args.host}:{args.port}",)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping UI server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
