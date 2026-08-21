"""Host discovery with injectable probes."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .constants import DEFERRED_OS, SUPPORTED_OS, TOOL_NAMES
from .models import HostObservation, ToolFact
from .paths import default_workspace


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class Probe(Protocol):
    def which(self, name: str) -> str | None: ...

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: float = 8.0,
    ) -> CommandResult: ...

    def exists(self, path: Path) -> bool: ...

    def read_text(self, path: Path) -> str | None: ...

    def env(self, name: str) -> str | None: ...

    def now(self) -> datetime: ...

    def system(self) -> str: ...

    def release(self) -> str: ...

    def machine(self) -> str: ...

    def cpu_count(self) -> int | None: ...

    def disk_usage(self, path: Path) -> tuple[int, int] | None: ...

    def hostname(self) -> str | None: ...


class SystemProbe:
    """Real host probe. Tests inject a fake instead of this type."""

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = dict(environ) if environ is not None else dict(os.environ)

    def which(self, name: str) -> str | None:
        return shutil.which(name)

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: float = 8.0,
    ) -> CommandResult:
        try:
            completed = subprocess.run(
                list(argv),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=dict(self._environ),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return CommandResult(tuple(argv), 127, "", str(exc))
        return CommandResult(
            tuple(argv),
            int(completed.returncode),
            completed.stdout or "",
            completed.stderr or "",
        )

    def exists(self, path: Path) -> bool:
        try:
            return path.exists()
        except OSError:
            return False

    def read_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None

    def env(self, name: str) -> str | None:
        return self._environ.get(name)

    def now(self) -> datetime:
        return datetime.now(UTC)

    def system(self) -> str:
        return platform.system()

    def release(self) -> str:
        return platform.release()

    def machine(self) -> str:
        return platform.machine()

    def cpu_count(self) -> int | None:
        return os.cpu_count()

    def disk_usage(self, path: Path) -> tuple[int, int] | None:
        try:
            usage = shutil.disk_usage(path)
        except OSError:
            return None
        return int(usage.total), int(usage.free)

    def hostname(self) -> str | None:
        try:
            return platform.node() or None
        except OSError:
            return None


def normalize_os(system: str) -> str:
    lowered = system.lower()
    if lowered == "linux":
        return "linux"
    if lowered == "windows" or lowered.startswith("cygwin"):
        return "windows"
    if lowered == "darwin":
        return "macos"
    return "unknown"


def normalize_arch(machine: str) -> str:
    lowered = machine.lower()
    if lowered in {"x86_64", "amd64", "x64"}:
        return "x86_64"
    if lowered in {"aarch64", "arm64"}:
        return "aarch64"
    if lowered.startswith("arm"):
        return "arm64"
    return lowered or "unknown"


def _parse_os_release(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        key, raw = line.split("=", 1)
        values[key] = raw.strip().strip('"')
    return values


def _linux_distro(probe: Probe) -> tuple[str, str]:
    text = probe.read_text(Path("/etc/os-release"))
    if not text:
        return "", ""
    values = _parse_os_release(text)
    name = values.get("PRETTY_NAME") or values.get("NAME") or ""
    version = values.get("VERSION_ID") or values.get("VERSION") or ""
    identifier = (values.get("ID") or "").lower()
    if "raspbian" in identifier or "raspberry" in name.lower():
        return "raspberry-pi", version or name
    if identifier:
        return identifier, version or name
    return name.lower(), version


def _tool_version(probe: Probe, path: str, name: str) -> str | None:
    argv = [path, "--version"]
    if name == "nvidia-smi":
        argv = [path, "--version"]
    result = probe.run(argv, timeout=5.0)
    if result.returncode != 0:
        return None
    line = (result.stdout or result.stderr).splitlines()
    return line[0].strip() if line else None


def _ram_bytes(probe: Probe, system: str) -> int | None:
    if system == "linux":
        text = probe.read_text(Path("/proc/meminfo"))
        if not text:
            return None
        for line in text.splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    return int(parts[1]) * 1024
        return None
    return None


def _gpus(probe: Probe) -> list[dict[str, object]]:
    path = probe.which("nvidia-smi")
    if not path:
        return []
    result = probe.run(
        [
            path,
            "--query-gpu=name,driver_version,memory.total",
            "--format=csv,noheader,nounits",
        ],
        timeout=5.0,
    )
    if result.returncode != 0:
        return []
    gpus: list[dict[str, object]] = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            continue
        memory = None
        if len(parts) >= 3 and parts[2].replace(".", "", 1).isdigit():
            memory = int(float(parts[2]) * 1024 * 1024)
        gpus.append(
            {
                "name": parts[0],
                "vendor": "nvidia",
                "driver": parts[1],
                "memory_bytes": memory,
            }
        )
    return gpus


def discover_host(
    probe: Probe | None = None,
    *,
    workspace: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> HostObservation:
    active = probe or SystemProbe(environ)
    os_name = normalize_os(active.system())
    arch = normalize_arch(active.machine())
    distro = ""
    version = active.release()
    pretty = active.system()
    if os_name == "linux":
        distro, pretty_version = _linux_distro(active)
        pretty = pretty_version or pretty
        version = pretty_version or version
        if distro == "raspberry-pi":
            pass
    support = "unknown"
    note = ""
    if os_name in SUPPORTED_OS:
        support = "supported"
        if os_name == "linux" and distro == "fedora":
            note = "Fedora is a first-class development target."
        elif os_name == "linux" and distro == "raspberry-pi":
            note = "Raspberry Pi OS / ARM is an intended worker platform."
        elif os_name == "windows":
            note = (
                "Windows support is implemented in bootstrap logic; "
                "host-test coverage is recorded separately."
            )
    elif os_name in DEFERRED_OS:
        support = "deferred"
        note = "macOS is architecturally representable but not presently implemented or tested."
    else:
        support = "unsupported"
        note = f"OS {os_name!r} is not a current MNCS bootstrap target."

    tools: dict[str, ToolFact] = {}
    python_names = ("python3", "python")
    for name in TOOL_NAMES:
        path = active.which(name)
        if name == "python" and not path:
            path = active.which("python3")
        if name == "python3" and not path:
            path = active.which("python")
        available = bool(path)
        version_text = _tool_version(active, path, name) if path else None
        tools[name] = ToolFact(
            name=name,
            available=available,
            path=path,
            version=version_text,
            status="healthy" if available else "absent",
        )
    # Prefer python3 facts when both exist.
    if tools.get("python3") and tools["python3"].available:
        tools["python"] = ToolFact(
            name="python",
            available=True,
            path=tools["python3"].path,
            version=tools["python3"].version,
            status="healthy",
        )

    disk = active.disk_usage(workspace or Path.cwd())
    ram = _ram_bytes(active, os_name)
    warnings: list[str] = []
    python_ok = any(tools[name].available for name in python_names if name in tools)
    if not python_ok:
        warnings.append(
            "Python 3.11+ is required for the MNCS validator and most family components."
        )
    if not tools["git"].available:
        warnings.append("Git is required to clone family repositories.")

    workspace_path = workspace if workspace is not None else default_workspace(environ)
    return HostObservation(
        os=os_name,
        architecture=arch,
        support=support,
        captured_at=active.now().isoformat().replace("+00:00", "Z"),
        os_name=pretty,
        os_version=version,
        distro=distro,
        support_note=note,
        hostname_present=active.hostname() is not None,
        tools=tools,
        cpu_count=active.cpu_count(),
        ram_bytes=ram,
        disk_total_bytes=disk[0] if disk else None,
        disk_free_bytes=disk[1] if disk else None,
        gpus=_gpus(active),
        workspace=str(workspace_path),
        warnings=warnings,
    )
