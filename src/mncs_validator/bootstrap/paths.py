"""Workspace, config, and state locations. Never assume a developer machine path."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


def _home() -> Path:
    return Path.home()


def xdg_config_home(environ: Mapping[str, str] | None = None) -> Path:
    env = environ if environ is not None else os.environ
    override = env.get("XDG_CONFIG_HOME")
    if override:
        return Path(override)
    if os.name == "nt":
        appdata = env.get("APPDATA")
        if appdata:
            return Path(appdata)
        return _home() / "AppData" / "Roaming"
    return _home() / ".config"


def xdg_state_home(environ: Mapping[str, str] | None = None) -> Path:
    env = environ if environ is not None else os.environ
    override = env.get("XDG_STATE_HOME")
    if override:
        return Path(override)
    if os.name == "nt":
        local = env.get("LOCALAPPDATA")
        if local:
            return Path(local)
        return _home() / "AppData" / "Local"
    return _home() / ".local" / "state"


def xdg_data_home(environ: Mapping[str, str] | None = None) -> Path:
    env = environ if environ is not None else os.environ
    override = env.get("XDG_DATA_HOME")
    if override:
        return Path(override)
    if os.name == "nt":
        local = env.get("LOCALAPPDATA")
        if local:
            return Path(local)
        return _home() / "AppData" / "Local"
    return _home() / ".local" / "share"


def expand_user_path(path: str, environ: Mapping[str, str] | None = None) -> Path:
    """Expand ~ without inheriting a hard-coded workspace."""

    raw = Path(path)
    if path.startswith("~/"):
        return _home() / path[2:]
    if environ is not None:
        return Path(os.path.expandvars(str(raw)))
    return Path(os.path.expanduser(path))


@dataclass(frozen=True)
class LocationLayout:
    """Resolved bootstrap locations for one invocation."""

    workspace: Path
    config_dir: Path
    state_dir: Path
    receipts_dir: Path
    workspace_config: Path

    def ensure_state(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)


def default_workspace(environ: Mapping[str, str] | None = None) -> Path:
    env = environ if environ is not None else os.environ
    override = env.get("MNCS_WORKSPACE")
    if override:
        return Path(override).expanduser()
    configured = xdg_config_home(env) / "mncs" / "workspace.json"
    if configured.is_file():
        try:
            payload = json.loads(configured.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = None
        if isinstance(payload, dict):
            value = payload.get("workspace")
            if isinstance(value, str) and value.strip():
                return Path(value).expanduser()
    return _home() / "mncs"


def layout_for(
    workspace: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> LocationLayout:
    env = environ if environ is not None else os.environ
    root = workspace if workspace is not None else default_workspace(env)
    config_dir = xdg_config_home(env) / "mncs"
    state_dir = xdg_state_home(env) / "mncs" / "bootstrap"
    return LocationLayout(
        workspace=root.expanduser(),
        config_dir=config_dir,
        state_dir=state_dir,
        receipts_dir=state_dir / "receipts",
        workspace_config=config_dir / "workspace.json",
    )
