from __future__ import annotations

import json
import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal

from aura.redaction import redact_sensitive_text


Callback = Callable[[Any], None]


@dataclass
class _PendingRequest:
    method: str
    callback: Callback
    error_callback: Callback
    timer: QTimer


def redact_diagnostic(value: str) -> str:
    return redact_sensitive_text(str(value)[:8000])


class JsonLineRpcClient(QObject):
    """Asynchronous JSONL request client for Codex app-server stdio."""

    started = pyqtSignal()
    stopped = pyqtSignal(int)
    crashed = pyqtSignal(str)
    state_changed = pyqtSignal(str)
    notification_received = pyqtSignal(str, object)
    server_request_received = pyqtSignal(object, str, object)
    protocol_error = pyqtSignal(str)
    stderr_ready = pyqtSignal(str)

    def __init__(
        self,
        *,
        request_timeout_ms: int = 30_000,
        startup_timeout_ms: int = 10_000,
        max_message_bytes: int = 8 * 1024 * 1024,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.request_timeout_ms = max(1, request_timeout_ms)
        self.startup_timeout_ms = max(1, startup_timeout_ms)
        self.max_message_bytes = max(1024, max_message_bytes)
        self.process = QProcess(self)
        self._isolated_process_group = False
        if os.name == "posix":
            parameters = QProcess.UnixProcessParameters()
            parameters.flags = QProcess.UnixProcessFlag(
                sum(
                    flag.value
                    for flag in (
                        QProcess.UnixProcessFlag.CreateNewSession,
                        QProcess.UnixProcessFlag.ResetSignalHandlers,
                        QProcess.UnixProcessFlag.CloseFileDescriptors,
                        QProcess.UnixProcessFlag.DisableCoreDumps,
                    )
                )
            )
            parameters.lowestFileDescriptorToClose = 3
            self.process.setUnixProcessParameters(parameters)
            self._isolated_process_group = True
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.process.started.connect(self._on_started)
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_process_error)
        self._startup_timer = QTimer(self)
        self._startup_timer.setSingleShot(True)
        self._startup_timer.timeout.connect(self._startup_timed_out)
        self._buffer = bytearray()
        self._next_request_id = 1
        self._pending: dict[int, _PendingRequest] = {}
        self._closing = False

    def start(self, program: str, arguments: list[str], cwd: str | Path) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            raise RuntimeError("The Codex app-server process is already active.")
        working_directory = Path(cwd).expanduser().resolve(strict=True)
        if not working_directory.is_dir():
            raise ValueError("Codex working directory must be a directory.")
        self._closing = False
        self._buffer.clear()
        self.process.setProgram(program)
        self.process.setArguments(list(arguments))
        self.process.setWorkingDirectory(str(working_directory))
        self.state_changed.emit("starting")
        self._startup_timer.start(self.startup_timeout_ms)
        self.process.start()

    def request(
        self,
        method: str,
        params: dict[str, Any] | None,
        callback: Callback,
        error_callback: Callback,
        *,
        timeout_ms: int | None = None,
    ) -> int:
        request_id = self._next_request_id
        self._next_request_id += 1
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._request_timed_out(request_id))
        self._pending[request_id] = _PendingRequest(
            method=method,
            callback=callback,
            error_callback=error_callback,
            timer=timer,
        )
        try:
            self._write({"id": request_id, "method": method, "params": params or {}})
        except Exception:
            self._pending.pop(request_id, None)
            timer.deleteLater()
            raise
        timer.start(timeout_ms or self.request_timeout_ms)
        return request_id

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        message: dict[str, Any] = {"method": method}
        if params:
            message["params"] = params
        self._write(message)

    def respond(
        self,
        request_id: int | str,
        *,
        result: Any = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        if error is not None:
            self._write({"id": request_id, "error": error})
        else:
            self._write({"id": request_id, "result": result})

    def cancel_request(self, request_id: int, reason: str = "Request cancelled.") -> None:
        pending = self._pending.pop(request_id, None)
        if pending is None:
            return
        pending.timer.stop()
        pending.timer.deleteLater()
        pending.error_callback(reason)

    def shutdown(self) -> None:
        self._closing = True
        self._startup_timer.stop()
        for request_id in tuple(self._pending):
            self.cancel_request(request_id, "Codex app-server stopped.")
        if self.process.state() == QProcess.ProcessState.NotRunning:
            return
        self.state_changed.emit("stopping")
        pid = int(self.process.processId())
        self._terminate_process_tree(pid, signal.SIGTERM)
        if not self.process.waitForFinished(1000):
            self._terminate_process_tree(
                pid,
                getattr(signal, "SIGKILL", signal.SIGTERM),
                force=True,
            )
            self.process.waitForFinished(1000)

    def _terminate_process_tree(
        self,
        pid: int,
        sig: signal.Signals,
        *,
        force: bool = False,
    ) -> None:
        if self._isolated_process_group and pid > 1:
            try:
                if os.getpgid(pid) == pid:
                    os.killpg(pid, sig)
                    return
            except (OSError, ProcessLookupError):
                return
        if os.name == "nt" and force and pid > 0:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
                timeout=5,
            )
            return
        if not force:
            self.process.terminate()
        else:
            self.process.kill()

    def _write(self, message: dict[str, Any]) -> None:
        if self.process.state() != QProcess.ProcessState.Running:
            raise RuntimeError("Codex app-server is not running.")
        encoded = (
            json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            + b"\n"
        )
        if len(encoded) > self.max_message_bytes:
            raise ValueError("JSON-RPC message exceeds the configured size limit.")
        if self.process.write(encoded) < 0:
            raise RuntimeError("Could not write to Codex app-server.")

    def _on_started(self) -> None:
        self._startup_timer.stop()
        self.state_changed.emit("initializing")
        self.started.emit()

    def _read_stdout(self) -> None:
        self._buffer.extend(bytes(self.process.readAllStandardOutput()))
        if len(self._buffer) > self.max_message_bytes and b"\n" not in self._buffer:
            self._buffer.clear()
            self.protocol_error.emit("JSON-RPC line exceeds the configured size limit.")
            return
        while b"\n" in self._buffer:
            raw, _, remainder = self._buffer.partition(b"\n")
            self._buffer = bytearray(remainder)
            if not raw.strip():
                continue
            if len(raw) > self.max_message_bytes:
                self.protocol_error.emit("JSON-RPC line exceeds the configured size limit.")
                continue
            try:
                message = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.protocol_error.emit("Invalid JSON received from Codex app-server.")
                continue
            if not isinstance(message, dict):
                self.protocol_error.emit("Codex app-server message must be a JSON object.")
                continue
            self._dispatch(message)

    def _dispatch(self, message: dict[str, Any]) -> None:
        if "id" in message and ("result" in message or "error" in message):
            request_id = message["id"]
            if not isinstance(request_id, int):
                self.protocol_error.emit("Unexpected JSON-RPC response ID.")
                return
            pending = self._pending.pop(request_id, None)
            if pending is None:
                self.protocol_error.emit("Response received for an unknown JSON-RPC request.")
                return
            pending.timer.stop()
            pending.timer.deleteLater()
            if "error" in message:
                error = message.get("error")
                if isinstance(error, dict):
                    safe_error = (
                        f"{error.get('code', 'error')}: "
                        f"{redact_diagnostic(str(error.get('message') or 'Request failed.'))}"
                    )
                else:
                    safe_error = "Codex app-server returned a malformed error."
                pending.error_callback(safe_error)
            else:
                pending.callback(message.get("result"))
            return
        method = message.get("method")
        if not isinstance(method, str) or not method:
            self.protocol_error.emit("Codex app-server message has no method or response.")
            return
        params = message.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            self.protocol_error.emit(f"JSON-RPC params for {method} must be an object.")
            return
        if "id" in message:
            self.server_request_received.emit(message["id"], method, params)
        else:
            self.notification_received.emit(method, params)

    def _read_stderr(self) -> None:
        value = bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace")
        if value:
            self.stderr_ready.emit(redact_diagnostic(value))

    def _request_timed_out(self, request_id: int) -> None:
        pending = self._pending.pop(request_id, None)
        if pending is None:
            return
        pending.timer.deleteLater()
        pending.error_callback(f"JSON-RPC request timed out: {pending.method}")

    def _startup_timed_out(self) -> None:
        self.protocol_error.emit("Codex app-server startup timed out.")
        self.shutdown()

    def _on_finished(self, exit_code: int, exit_status) -> None:
        self._startup_timer.stop()
        for request_id in tuple(self._pending):
            self.cancel_request(request_id, "Codex app-server exited before responding.")
        self.state_changed.emit("stopped")
        self.stopped.emit(exit_code)
        if not self._closing and (
            exit_code != 0 or exit_status == QProcess.ExitStatus.CrashExit
        ):
            self.crashed.emit(f"Codex app-server exited with code {exit_code}.")

    def _on_process_error(self, error) -> None:
        if self._closing:
            return
        if error == QProcess.ProcessError.FailedToStart:
            self._startup_timer.stop()
            self.crashed.emit("Codex app-server failed to start.")
