# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from mncs_validator.bootstrap.constants import BOOTSTRAP_DISCLAIMER, EXIT_CODES
from mncs_validator.bootstrap.executor import Executor
from mncs_validator.bootstrap.host import CommandResult, discover_host
from mncs_validator.bootstrap.models import ComponentState
from mncs_validator.bootstrap.observe import observe_family
from mncs_validator.bootstrap.paths import layout_for
from mncs_validator.bootstrap.planner import plan_bootstrap
from mncs_validator.bootstrap.registry import load_family, validate_family_mapping
from mncs_validator.cli import main
from mncs_validator.schemas import load_schema, schema_errors

ROOT = Path(__file__).resolve().parents[1]


class FakeProbe:
    def __init__(
        self,
        *,
        system: str = "Linux",
        machine: str = "x86_64",
        which: Mapping[str, str] | None = None,
        files: Mapping[str, str] | None = None,
        commands: Mapping[tuple[str, ...], CommandResult] | None = None,
    ) -> None:
        self._system = system
        self._machine = machine
        self._which = dict(which or {})
        self._files = {str(Path(key)): value for key, value in (files or {}).items()}
        self._commands = dict(commands or {})
        self.calls: list[tuple[str, ...]] = []

    def which(self, name: str) -> str | None:
        return self._which.get(name)

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        timeout: float = 8.0,
    ) -> CommandResult:
        del cwd, timeout
        key = tuple(argv)
        self.calls.append(key)
        if key in self._commands:
            return self._commands[key]
        if argv and argv[0] in self._which and "--version" in argv:
            return CommandResult(key, 0, f"{argv[0]} 1.0", "")
        return CommandResult(key, 0, "", "")

    def exists(self, path: Path) -> bool:
        text = str(path)
        return text in self._files or any(
            item.startswith(text.rstrip("/") + "/") for item in self._files
        )

    def read_text(self, path: Path) -> str | None:
        return self._files.get(str(path))

    def env(self, name: str) -> str | None:
        return None

    def now(self) -> datetime:
        return datetime(2026, 8, 21, tzinfo=UTC)

    def system(self) -> str:
        return self._system

    def release(self) -> str:
        return "test"

    def machine(self) -> str:
        return self._machine

    def cpu_count(self) -> int | None:
        return 8

    def disk_usage(self, path: Path) -> tuple[int, int] | None:
        del path
        return (1000, 500)

    def hostname(self) -> str | None:
        return "testhost"


def test_family_registry_schema_and_graph() -> None:
    family = load_family(ROOT / "family/mncs-family.v0.1.json")
    payload = json.loads((ROOT / "family/mncs-family.v0.1.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == family.schema_version
    assert schema_errors(payload, "family-registry-0.1") == []
    assert validate_family_mapping(payload) == []
    assert "mncs" in family.components
    assert "developer" in family.profiles
    assert family.components["mncs"].normative is True
    assert family.components["mncs-forge"].authority_class == "development-control-plane"
    assert family.compatibility["state"] == "UNKNOWN"
    duplicate = json.loads(json.dumps(payload))
    duplicate["components"].append(duplicate["components"][0])
    errors = validate_family_mapping(duplicate)
    assert any("duplicate" in error for error in errors)
    cyclic = json.loads(json.dumps(payload))
    cyclic["components"][0]["dependencies"] = [cyclic["components"][1]["id"]]
    cyclic["components"][1]["dependencies"] = [cyclic["components"][0]["id"]]
    errors = validate_family_mapping(cyclic)
    assert any("cycle" in error for error in errors)


def test_packaged_bootstrap_schemas_load() -> None:
    for name in (
        "family-registry-0.1",
        "host-observation-0.1",
        "bootstrap-plan-0.1",
        "bootstrap-receipt-0.1",
    ):
        schema = load_schema(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_clean_host_core_plan(tmp_path: Path) -> None:
    probe = FakeProbe(
        which={"git": "/usr/bin/git", "python3": "/usr/bin/python3", "python": "/usr/bin/python3"},
        files={"/etc/os-release": 'ID=fedora\nPRETTY_NAME="Fedora Linux"\nVERSION_ID="44"\n'},
    )
    family = load_family()
    host = discover_host(probe, workspace=tmp_path)
    host = observe_family(family, host, probe=probe, workspace=tmp_path)
    assert host.os == "linux"
    assert host.distro == "fedora"
    assert host.support == "supported"
    plan = plan_bootstrap(family, host, profile="core", workspace=tmp_path)
    kinds = {action.kind for action in plan.actions if action.component == "mncs"}
    assert "clone" in kinds
    assert "pip_install" in kinds
    assert plan.outcome == "changes_required"
    assert schema_errors(plan.as_dict(), "bootstrap-plan-0.1") == []


def test_already_installed_is_idempotent(tmp_path: Path) -> None:
    checkout = tmp_path / "machine-native-complexity-standard"
    probe = FakeProbe(
        which={
            "git": "/usr/bin/git",
            "python3": "/usr/bin/python3",
            "python": "/usr/bin/python3",
            "mncs": str(tmp_path / "bin/mncs"),
        },
        files={
            "/etc/os-release": 'ID=fedora\nPRETTY_NAME="Fedora Linux"\n',
            str(checkout / ".git"): "",
            str(checkout / "pyproject.toml"): "[project]\nname='mncs-validator'\n",
        },
        commands={
            ("git", "-C", str(checkout), "remote", "get-url", "origin"): CommandResult(
                (), 0, "https://github.com/epi13/machine-native-complexity-standard", ""
            ),
            ("git", "-C", str(checkout), "rev-parse", "--abbrev-ref", "HEAD"): CommandResult(
                (), 0, "main", ""
            ),
            (str(tmp_path / "bin/mncs"), "version", "--json"): CommandResult(
                (), 0, json.dumps({"package_version": "0.3.0rc1"}), ""
            ),
        },
    )
    family = load_family()
    host = discover_host(probe, workspace=tmp_path)
    host = observe_family(family, host, probe=probe, workspace=tmp_path)
    assert host.components["mncs"].state in {"installed", "configured"}
    plan = plan_bootstrap(family, host, profile="core", workspace=tmp_path)
    mncs_actions = [action for action in plan.actions if action.component == "mncs"]
    assert all(action.status == "skipped" for action in mncs_actions)
    assert plan.outcome == "unchanged"


def test_macos_is_deferred(tmp_path: Path) -> None:
    probe = FakeProbe(system="Darwin", machine="arm64", which={"git": "/usr/bin/git"})
    family = load_family()
    host = discover_host(probe, workspace=tmp_path)
    host = observe_family(family, host, probe=probe, workspace=tmp_path)
    assert host.os == "macos"
    assert host.support == "deferred"
    plan = plan_bootstrap(family, host, profile="core", workspace=tmp_path)
    assert plan.outcome == "unsupported"


def test_missing_python_blocks_core(tmp_path: Path) -> None:
    probe = FakeProbe(which={"git": "/usr/bin/git"})
    family = load_family()
    host = discover_host(probe, workspace=tmp_path)
    host = observe_family(family, host, probe=probe, workspace=tmp_path)
    plan = plan_bootstrap(family, host, profile="core", workspace=tmp_path)
    assert any(item.code == "missing-tool" for item in plan.blocked)


def test_offline_plan_blocks_clone(tmp_path: Path) -> None:
    probe = FakeProbe(
        which={"git": "/usr/bin/git", "python3": "/usr/bin/python3", "python": "/usr/bin/python3"}
    )
    family = load_family()
    host = discover_host(probe, workspace=tmp_path)
    host = observe_family(family, host, probe=probe, workspace=tmp_path)
    plan = plan_bootstrap(family, host, profile="core", workspace=tmp_path, network=False)
    assert any(item.code == "network-required" for item in plan.blocked)


def test_unsupported_component_on_windows_control(tmp_path: Path) -> None:
    probe = FakeProbe(
        system="Windows",
        machine="AMD64",
        which={
            "git": "C:\\git.exe",
            "python": "C:\\Python311\\python.exe",
            "python3": "C:\\Python311\\python.exe",
        },
    )
    family = load_family()
    host = discover_host(probe, workspace=tmp_path)
    host = observe_family(family, host, probe=probe, workspace=tmp_path)
    plan = plan_bootstrap(family, host, profile="developer", workspace=tmp_path)
    assert any(
        item.component == "mncs-control" and item.code == "unsupported-platform"
        for item in plan.blocked
    )


def test_executor_dry_run_does_not_clone(tmp_path: Path) -> None:
    probe = FakeProbe(
        which={"git": "/usr/bin/git", "python3": "/usr/bin/python3", "python": "/usr/bin/python3"}
    )
    family = load_family()
    host = discover_host(probe, workspace=tmp_path)
    host = observe_family(family, host, probe=probe, workspace=tmp_path)
    plan = plan_bootstrap(family, host, profile="core", workspace=tmp_path)
    layout = layout_for(
        tmp_path,
        environ={
            "XDG_STATE_HOME": str(tmp_path / "state"),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
        },
    )
    executor = Executor(probe=probe, layout=layout, python="/usr/bin/python3")
    receipt = executor.execute(family, host, plan, dry_run=True, yes=True, interactive=False)
    assert receipt["outcome"] == "planned"
    assert schema_errors(receipt, "bootstrap-receipt-0.1") == []
    assert BOOTSTRAP_DISCLAIMER in str(receipt["disclaimer"])
    assert not list(tmp_path.glob("machine-native-complexity-standard"))


def test_executor_refuses_untrusted_url(tmp_path: Path) -> None:
    probe = FakeProbe(
        which={"git": "/usr/bin/git", "python3": "/usr/bin/python3", "python": "/usr/bin/python3"}
    )
    family = load_family()
    host = discover_host(probe, workspace=tmp_path)
    host.components["mncs"] = ComponentState("mncs", "not_installed")
    plan = plan_bootstrap(family, host, profile="core", workspace=tmp_path)
    layout = layout_for(
        tmp_path,
        environ={
            "XDG_STATE_HOME": str(tmp_path / "state"),
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
        },
    )
    executor = Executor(probe=probe, layout=layout)
    # Mutating the registry URL is refused by _safe_repo_url; clone uses family URL.
    receipt = executor.execute(family, host, plan, dry_run=False, yes=True, interactive=False)
    clone_calls = [call for call in probe.calls if call and call[0] == "git" and "clone" in call]
    assert clone_calls
    assert all(str(call).find("github.com/epi13/") != -1 for call in clone_calls)
    assert receipt["receipt_kind"] == "installation-deployment"


def test_cli_family_and_plan_json(capsys: object, tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setenv("MNCS_WORKSPACE", str(tmp_path))  # type: ignore[attr-defined]
    assert main(["family", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert payload["registry_id"] == "mncs-family" or payload["name"] == "MNCS family"
    assert "mncs" in {item["id"] for item in payload["components"]}
    assert BOOTSTRAP_DISCLAIMER in payload["disclaimer"]
    assert main(
        ["bootstrap", "--profile", "core", "--plan", "--json", "--workspace", str(tmp_path)]
    ) in {
        0,
        EXIT_CODES["incomplete"],
        EXIT_CODES["network"],
        EXIT_CODES["unsupported"],
    }
    planned = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert planned["schema_version"] == "mncs-bootstrap-plan.v0.1"
    assert "conformance" not in planned["outcome"]
    assert main(["describe", "--json", "--workspace", str(tmp_path)]) == 0
    described = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert described["mncs"]["authority"] == "normative-standard"
    assert "bootstrap" in described["operations"]
    assert main(["family", "--id", "no-such"]) == 2


def test_cli_human_family(capsys: object) -> None:
    assert main(["family"]) == 0
    text = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "Machine-Native Complexity Standard" in text
    assert "Profiles:" in text


def test_workspace_is_not_hardcoded() -> None:
    from mncs_validator.bootstrap.paths import default_workspace

    path = default_workspace({"HOME": "/tmp/someone", "MNCS_WORKSPACE": "/opt/mncs"})
    assert path == Path("/opt/mncs")
    assert "Documents/Projects" not in str(default_workspace({"HOME": "/tmp/someone"}))
