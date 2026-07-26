"""Explicit, bounded MNCS Provider Protocol 0.1 client."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

from .canonical import canonicalize
from .errors import MncsError

MAX_PROVIDER_OUTPUT = 4 * 1024 * 1024
DEFAULT_TIMEOUT = 30.0


def verify_result(result: dict[str, Any]) -> list[str]:
    """Validate one provider response without treating UNKNOWN as PASS."""

    errors: list[str] = []
    if result.get("protocol_version") != "0.1":
        errors.append("protocol_version must be 0.1")
    if result.get("type") not in {
        "capabilities",
        "analysis_response",
        "health_response",
        "error",
        "cancelled",
    }:
        errors.append("unsupported response type")
    status = result.get("status")
    if result.get("type") == "analysis_response" and status not in {"PASS", "FAIL", "UNKNOWN"}:
        errors.append("analysis status must be PASS, FAIL, or UNKNOWN")
    if not isinstance(result.get("provider"), dict):
        errors.append("provider identity must be an object")
    if not isinstance(result.get("extensions", {}), dict):
        errors.append("extensions must be an object")
    return sorted(errors)


def _parse_protocol_stdout(content: bytes) -> dict[str, Any]:
    if len(content) > MAX_PROVIDER_OUTPUT:
        raise MncsError("provider stdout exceeded the configured cap")
    try:
        text = content.decode("utf-8")
    except UnicodeError as exc:
        raise MncsError("provider stdout is not UTF-8") from exc
    lines = text.splitlines()
    if len(lines) != 1 or not lines[0]:
        raise MncsError("provider must emit exactly one JSON Lines response")
    try:
        value: Any = json.loads(lines[0])
    except json.JSONDecodeError as exc:
        raise MncsError(f"provider emitted nonprotocol stdout: {exc}") from exc
    if not isinstance(value, dict):
        raise MncsError("provider response must be an object")
    errors = verify_result(value)
    if errors:
        raise MncsError("invalid provider response: " + "; ".join(errors))
    return value


def _terminate_provider(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGTERM)
    else:
        process.terminate()
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def _bounded_reader(
    stream: Any,
    destination: bytearray,
    overflow: threading.Event,
) -> None:
    while chunk := stream.read(64 * 1024):
        if overflow.is_set():
            continue
        remaining = MAX_PROVIDER_OUTPUT + 1 - len(destination)
        destination.extend(chunk[:remaining])
        if len(destination) > MAX_PROVIDER_OUTPUT:
            overflow.set()


def run_provider(
    command: list[str],
    request: dict[str, Any],
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Run an explicitly requested provider without a shell in an isolated workspace."""

    if not command or any(not item for item in command):
        raise MncsError("provider command must be a non-empty argument array")
    if timeout <= 0:
        raise MncsError("provider timeout must be positive")
    payload = canonicalize(request) + b"\n"
    with tempfile.TemporaryDirectory(prefix="mncs-provider-") as temporary:
        process = subprocess.Popen(
            command,
            cwd=temporary,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
            env={
                "PATH": os.environ.get("PATH", ""),
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "MNCS_PROVIDER_WORKSPACE": temporary,
            },
        )
        stdout = bytearray()
        stderr = bytearray()
        overflow = threading.Event()
        stdout_thread = threading.Thread(
            target=_bounded_reader,
            args=(process.stdout, stdout, overflow),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_bounded_reader,
            args=(process.stderr, stderr, overflow),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()
        try:
            if process.stdin is None:
                raise MncsError("provider stdin was not created")
            process.stdin.write(payload)
            process.stdin.close()
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _terminate_provider(process)
            raise MncsError(f"provider timed out after {timeout:g} seconds") from exc
        except BaseException:
            _terminate_provider(process)
            raise
        stdout_thread.join(timeout=1.0)
        stderr_thread.join(timeout=1.0)
        if overflow.is_set():
            _terminate_provider(process)
            raise MncsError("provider output exceeded the configured cap")
        if len(stderr) > MAX_PROVIDER_OUTPUT:
            raise MncsError("provider stderr exceeded the configured cap")
        if process.returncode != 0:
            excerpt = stderr[:4096].decode("utf-8", errors="replace")
            raise MncsError(f"provider exited {process.returncode}: {excerpt}")
        return _parse_protocol_stdout(bytes(stdout))


def load_descriptor(path: Path) -> dict[str, Any]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MncsError(f"cannot read provider descriptor: {exc}") from exc
    if not isinstance(value, dict):
        raise MncsError("provider descriptor must be an object")
    command = value.get("command")
    if (
        value.get("protocol_version") != "0.1"
        or not isinstance(command, list)
        or not command
        or not all(isinstance(item, str) and item for item in command)
    ):
        raise MncsError("invalid provider descriptor")
    return value


def inspect_provider(command: list[str], *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    request = {
        "protocol_version": "0.1",
        "type": "capabilities",
        "request_id": "mncs-inspect",
        "extensions": {},
    }
    return run_provider(command, request, timeout=timeout)


def run_descriptor(
    descriptor: Path, request: dict[str, Any], *, timeout: float | None = None
) -> dict[str, Any]:
    value = load_descriptor(descriptor)
    configured = value.get("timeout_seconds", DEFAULT_TIMEOUT)
    actual_timeout = timeout if timeout is not None else float(configured)
    return run_provider(list(value["command"]), request, timeout=actual_timeout)
