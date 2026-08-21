"""Execute a bootstrap plan through injectable adapters."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .constants import BOOTSTRAP_DISCLAIMER, GITHUB_HOST, RECEIPT_SCHEMA_VERSION
from .errors import BootstrapError, ConfirmationRequired
from .host import CommandResult, Probe, SystemProbe
from .models import BootstrapPlan, FamilyRegistry, HostObservation, PlanAction
from .paths import LocationLayout, layout_for
from .receipts import write_receipt


@dataclass
class ActionResult:
    id: str
    component: str
    kind: str
    result: str
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "component": self.component,
            "kind": self.kind,
            "result": self.result,
            "detail": self.detail,
        }


def _safe_repo_url(url: str) -> str:
    if not url.startswith(GITHUB_HOST):
        raise BootstrapError(f"refusing to clone untrusted URL: {url}")
    if any(char in url for char in " \n\r\t;|&"):
        raise BootstrapError(f"refusing to clone malformed URL: {url}")
    return url


def _safe_dest(workspace: Path, dest: Path) -> Path:
    workspace = workspace.resolve()
    dest = dest if dest.is_absolute() else (workspace / dest)
    try:
        dest.resolve().relative_to(workspace)
    except ValueError as exc:
        raise BootstrapError(f"refusing to write outside workspace: {dest}") from exc
    return dest


class Executor:
    def __init__(
        self,
        probe: Probe | None = None,
        *,
        layout: LocationLayout | None = None,
        python: str | None = None,
        confirm: Callable[[str], bool] | None = None,
    ) -> None:
        self.probe = probe or SystemProbe()
        self.layout = layout or layout_for()
        self.python = python or sys.executable
        self.confirm = confirm

    def _run(
        self, argv: Sequence[str], *, cwd: Path | None = None, timeout: float = 300.0
    ) -> CommandResult:
        return self.probe.run(argv, cwd=cwd, timeout=timeout)

    def _component_dir(self, family: FamilyRegistry, component_id: str) -> Path:
        component = family.component(component_id)
        return _safe_dest(self.layout.workspace, Path(component.repository.name))

    def execute(
        self,
        family: FamilyRegistry,
        host: HostObservation,
        plan: BootstrapPlan,
        *,
        dry_run: bool,
        yes: bool,
        interactive: bool,
    ) -> dict[str, object]:
        started = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        if plan.mutating() and not dry_run and not yes:
            if not interactive:
                raise ConfirmationRequired(
                    "refusing to mutate the host without --yes (non-interactive). "
                    "Re-run with --plan or --yes."
                )
            if self.confirm is not None and not self.confirm(
                "Proceed with the planned bootstrap actions?"
            ):
                raise ConfirmationRequired("operator declined bootstrap execution")
        results: list[ActionResult] = []
        failures: list[str] = []
        if not dry_run:
            self.layout.workspace.mkdir(parents=True, exist_ok=True)
            self.layout.ensure_state()
            self.layout.workspace_config.write_text(
                json.dumps({"workspace": str(self.layout.workspace)}, indent=2) + "\n",
                encoding="utf-8",
            )
        for action in plan.actions:
            if action.status in {"skipped", "blocked"}:
                results.append(
                    ActionResult(action.id, action.component, action.kind, "skipped", action.detail)
                )
                continue
            if action.status == "required_operator":
                results.append(
                    ActionResult(
                        action.id, action.component, action.kind, "skipped", action.summary
                    )
                )
                continue
            if dry_run:
                results.append(
                    ActionResult(
                        action.id, action.component, action.kind, "planned", action.summary
                    )
                )
                continue
            try:
                detail = self._apply(family, plan, action)
            except BootstrapError as exc:
                failures.append(str(exc))
                results.append(
                    ActionResult(action.id, action.component, action.kind, "failed", str(exc))
                )
                continue
            results.append(
                ActionResult(action.id, action.component, action.kind, "completed", detail)
            )
        completed = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        if dry_run:
            outcome = "planned"
        elif failures:
            outcome = "partial" if any(item.result == "completed" for item in results) else "failed"
        elif plan.outcome == "unchanged":
            outcome = "unchanged"
        else:
            outcome = "completed"
        receipt: dict[str, object] = {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "receipt_kind": "installation-deployment",
            "disclaimer": BOOTSTRAP_DISCLAIMER,
            "bootstrap_version": _package_version(),
            "requested": {
                "profile": plan.profile,
                "components": list(plan.components),
                "workspace": str(self.layout.workspace),
                "ref": plan.ref,
                "dry_run": dry_run,
            },
            "host": {
                "os": host.os,
                "os_name": host.os_name,
                "architecture": host.architecture,
                "fingerprint": _fingerprint(host),
            },
            "started_at": started,
            "completed_at": completed,
            "resolved_components": [
                {
                    "id": key,
                    "state": value.state,
                    "path": value.path,
                    "ref": value.ref,
                    "version": value.version,
                }
                for key, value in host.components.items()
            ],
            "actions": [item.as_dict() for item in results],
            "health": [value.as_dict() for value in host.mcp.values()],
            "warnings": list(plan.warnings),
            "failures": failures,
            "configuration_paths": [str(self.layout.workspace_config)],
            "outcome": outcome,
        }
        if not dry_run:
            write_receipt(self.layout.receipts_dir, receipt)
        return receipt

    def _apply(self, family: FamilyRegistry, plan: BootstrapPlan, action: PlanAction) -> str:
        dest = self._component_dir(family, action.component)
        component = family.component(action.component)
        if action.kind == "clone":
            url = _safe_repo_url(component.repository.url)
            if dest.exists():
                return f"existing checkout preserved at {dest}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            argv = ["git", "clone", "--", url, str(dest)]
            if plan.ref:
                argv = ["git", "clone", "--branch", plan.ref, "--", url, str(dest)]
            result = self._run(argv, timeout=600.0)
            if result.returncode != 0:
                raise BootstrapError(
                    result.stderr.strip() or f"git clone failed for {component.id}"
                )
            return f"cloned {url} -> {dest}"
        if action.kind == "create_venv":
            venv = dest / ".venv"
            if (venv / "bin" / "python").exists() or (venv / "Scripts" / "python.exe").exists():
                return f"venv already present at {venv}"
            result = self._run([self.python, "-m", "venv", str(venv)], timeout=120.0)
            if result.returncode != 0:
                raise BootstrapError(result.stderr.strip() or "venv creation failed")
            return f"created {venv}"
        if action.kind == "pip_install":
            python = dest / ".venv" / "bin" / "python"
            if not python.exists():
                windows = dest / ".venv" / "Scripts" / "python.exe"
                python = windows if windows.exists() else Path(self.python)
            spec = "."
            if component.package and component.package.extras:
                spec = f".[{component.package.extras}]"
            result = self._run(
                [str(python), "-m", "pip", "install", "-e", spec], cwd=dest, timeout=600.0
            )
            if result.returncode != 0:
                raise BootstrapError(
                    result.stderr.strip() or f"pip install failed for {component.id}"
                )
            return f"installed {spec} into {python}"
        if action.kind == "cargo_build":
            result = self._run(["cargo", "build", "--offline"], cwd=dest, timeout=30.0)
            if result.returncode != 0:
                result = self._run(["cargo", "build"], cwd=dest, timeout=900.0)
            if result.returncode != 0:
                raise BootstrapError(
                    result.stderr.strip() or f"cargo build failed for {component.id}"
                )
            return f"built {component.id} in {dest}"
        if action.kind == "enable_service":
            raise BootstrapError(
                f"{component.display_name} service enablement is operator-mediated; "
                "re-run the component installer explicitly"
            )
        if action.kind in {"health_check", "skip", "configure", "operator"}:
            return action.summary
        raise BootstrapError(f"unknown action kind: {action.kind}")


def _package_version() -> str:
    from .. import __version__

    return __version__


def _fingerprint(host: HostObservation) -> str:
    from hashlib import sha256

    material = f"{host.os}|{host.architecture}|{host.cpu_count or 0}".encode()
    return "sha256:" + sha256(material).hexdigest()


def persist_workspace_config(
    layout: LocationLayout, environ: Mapping[str, str] | None = None
) -> None:
    del environ
    layout.ensure_state()
    layout.workspace_config.write_text(
        json.dumps({"workspace": str(layout.workspace)}, indent=2) + "\n",
        encoding="utf-8",
    )
    os.environ.setdefault("MNCS_WORKSPACE", str(layout.workspace))
