"""Bootstrap CLI registration and dispatch."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .constants import BOOTSTRAP_DISCLAIMER, COMMANDS, EXIT_CODES
from .errors import BootstrapError
from .executor import Executor
from .host import discover_host
from .models import FamilyRegistry, HostObservation
from .observe import observe_family
from .paths import layout_for
from .planner import plan_bootstrap
from .registry import load_family
from .render import render_describe, render_family, render_host, render_plan, render_receipt


def _json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")


def _common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", type=Path, help="family checkout workspace (never assumed)")
    parser.add_argument(
        "--profile", help="installation profile: core, developer, worker, research, full"
    )
    parser.add_argument(
        "--component",
        action="append",
        default=[],
        dest="components",
        help="component id; repeatable",
    )
    parser.add_argument("--ref", help="explicit git ref for clones")
    parser.add_argument(
        "--no-network", action="store_true", help="plan/execute without network actions"
    )
    parser.add_argument(
        "--allow-services", action="store_true", help="include user-service actions in execution"
    )
    parser.add_argument("--verbose", action="store_true")
    _json_flag(parser)


def register_bootstrap_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    family = subparsers.add_parser("family", help="describe the MNCS family registry")
    family.add_argument("--id", dest="component_id", help="one component id")
    _json_flag(family)

    components = subparsers.add_parser("components", help="list family components")
    components.add_argument("--profile")
    components.add_argument("--all", action="store_true")
    _json_flag(components)

    describe = subparsers.add_parser("describe", help="machine-native self-description")
    describe.add_argument("--workspace", type=Path)
    _json_flag(describe)

    doctor = subparsers.add_parser("doctor", help="observe host and family health")
    doctor.add_argument("--workspace", type=Path)
    doctor.add_argument("--component")
    _json_flag(doctor)

    status = subparsers.add_parser("status", help="installed family status")
    status.add_argument("--workspace", type=Path)
    _json_flag(status)

    bootstrap = subparsers.add_parser("bootstrap", help="plan or apply an MNCS family installation")
    bootstrap.add_argument("bootstrap_command", nargs="?", choices=("plan", "apply"))
    bootstrap.add_argument("--plan", action="store_true")
    bootstrap.add_argument("--dry-run", action="store_true")
    bootstrap.add_argument("--yes", action="store_true")
    _common_flags(bootstrap)

    install = subparsers.add_parser("install", help="install selected profile or components")
    install.add_argument("--dry-run", action="store_true")
    install.add_argument("--yes", action="store_true")
    _common_flags(install)

    configure = subparsers.add_parser("configure", help="report remaining operator configuration")
    configure.add_argument("--component")
    configure.add_argument("--workspace", type=Path)
    _json_flag(configure)

    update = subparsers.add_parser("update", help="plan updates for installed components")
    update.add_argument("--yes", action="store_true")
    update.add_argument("--dry-run", action="store_true")
    update.add_argument("--all", action="store_true")
    _common_flags(update)

    repair = subparsers.add_parser("repair", help="re-plan from observed incomplete state")
    repair.add_argument("--yes", action="store_true")
    repair.add_argument("--dry-run", action="store_true")
    _common_flags(repair)

    deploy = subparsers.add_parser("deploy", help="deployment helpers")
    deploy_commands = deploy.add_subparsers(dest="deploy_command", required=True)
    worker = deploy_commands.add_parser("worker", help="plan Fabric worker bring-up")
    worker.add_argument("--yes", action="store_true")
    worker.add_argument("--plan", action="store_true")
    worker.add_argument("--dry-run", action="store_true")
    _common_flags(worker)

    uninstall = subparsers.add_parser("uninstall", help="report safe removal limits")
    uninstall.add_argument("--component", dest="component_id", required=True)
    uninstall.add_argument("--yes", action="store_true")
    uninstall.add_argument("--dry-run", action="store_true")
    uninstall.add_argument("--workspace", type=Path)
    _json_flag(uninstall)


def _emit(value: Any, *, json_mode: bool, text: str) -> int:
    if json_mode:
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print(text)
    return 0


def _load(workspace: Path | None) -> tuple[FamilyRegistry, HostObservation]:
    family = load_family()
    host = discover_host(workspace=workspace)
    host = observe_family(family, host, workspace=workspace)
    return family, host


def _plan_from_args(
    args: argparse.Namespace, *, default_profile: str | None
) -> tuple[FamilyRegistry, HostObservation, Any]:
    workspace = getattr(args, "workspace", None)
    family, host = _load(workspace)
    profile = getattr(args, "profile", None) or default_profile
    extras = list(getattr(args, "components", []) or [])
    if getattr(args, "component", None):
        extras.append(args.component)
    if not profile and not extras:
        profile = "core"
    plan = plan_bootstrap(
        family,
        host,
        profile=profile,
        extras=extras,
        network=not getattr(args, "no_network", False),
        allow_services=getattr(args, "allow_services", False),
        ref=getattr(args, "ref", None),
        workspace=workspace,
    )
    return family, host, plan


def _interactive_profile(host: HostObservation) -> str:
    print(render_host(host))
    print()
    print("Choose installation:")
    print("  [1] MNCS Core")
    print("  [2] Developer")
    print("  [3] Fabric Worker")
    print("  [4] Research")
    print("  [5] Full MNCS")
    print("  [6] Core (default)")
    print()
    choice = input("Profile [1-5, default 1]: ").strip() or "1"
    return {
        "1": "core",
        "2": "developer",
        "3": "worker",
        "4": "research",
        "5": "full",
        "6": "core",
    }.get(choice, "core")


def _exit_for_plan(plan: Any) -> int:
    if plan.outcome == "unsupported":
        return EXIT_CODES["unsupported"]
    if plan.outcome == "blocked":
        codes = {item.code for item in plan.blocked}
        if "privilege-required" in codes:
            return EXIT_CODES["privilege"]
        if "network-required" in codes:
            return EXIT_CODES["network"]
        if "unsupported-platform" in codes:
            return EXIT_CODES["unsupported"]
        return EXIT_CODES["incomplete"]
    return EXIT_CODES["ok"]


def run_bootstrap(args: argparse.Namespace) -> int:
    command = args.command
    json_mode = bool(getattr(args, "json", False))
    if command == "family":
        family = load_family()
        if getattr(args, "component_id", None):
            if args.component_id not in family.components:
                raise BootstrapError(f"unknown component: {args.component_id}")
            component = family.component(args.component_id)
            payload = component.as_dict()
            payload["disclaimer"] = BOOTSTRAP_DISCLAIMER
            return _emit(
                payload, json_mode=json_mode, text=f"{component.display_name}\n{component.purpose}"
            )
        payload = {
            "schema_version": family.schema_version,
            "registry_id": family.registry_id,
            "name": family.name,
            "description": family.description,
            "authority": family.authority,
            "compatibility": family.compatibility,
            "disclaimer": BOOTSTRAP_DISCLAIMER,
            "profiles": {
                key: {
                    "id": profile.id,
                    "display_name": profile.display_name,
                    "description": profile.description,
                    "components": list(profile.components),
                    "optional_components": list(profile.optional_components),
                }
                for key, profile in family.profiles.items()
            },
            "components": [component.as_dict() for component in family.components.values()],
        }
        return _emit(payload, json_mode=json_mode, text=render_family(family))
    if command == "components":
        family = load_family()
        ids = list(family.components)
        if args.profile:
            if args.profile not in family.profiles:
                raise BootstrapError(f"unknown profile: {args.profile}")
            ids = list(family.profile(args.profile).components)
            if args.all:
                ids.extend(family.profile(args.profile).optional_components)
        payload = {
            "disclaimer": BOOTSTRAP_DISCLAIMER,
            "profile": args.profile,
            "components": [family.component(item).as_dict() for item in ids],
        }
        text = "\n".join(
            f"{item['id']:24} {item['display_name']}" for item in payload["components"]
        )
        return _emit(payload, json_mode=json_mode, text=text)
    if command == "describe":
        family, host = _load(getattr(args, "workspace", None))
        payload = {
            "mncs": {
                "name": "Machine-Native Complexity Standard",
                "purpose": family.components["mncs"].purpose,
                "authority": "normative-standard",
                "repository": family.components["mncs"].repository.url,
            },
            "disclaimer": BOOTSTRAP_DISCLAIMER,
            "family": {
                "compatibility": family.compatibility,
                "components": [component.as_dict() for component in family.components.values()],
            },
            "host": host.as_dict(),
            "installed": {key: value.as_dict() for key, value in host.components.items()},
            "mcp": {key: value.as_dict() for key, value in host.mcp.items()},
            "services": host.services,
            "documentation": {
                "getting_started": "docs/getting-started.md",
                "family": "docs/family.md",
                "bootstrap": "docs/bootstrap.md",
                "ai_agents": "docs/ai-agent-bootstrap.md",
            },
            "configuration": {
                "workspace": host.workspace,
                "family_registry": "family/mncs-family.v0.1.json",
            },
            "operations": list(COMMANDS),
            "health": {key: value.state for key, value in host.components.items()},
        }
        return _emit(payload, json_mode=json_mode, text=render_describe(payload))
    if command in {"doctor", "status"}:
        family, host = _load(getattr(args, "workspace", None))
        if command == "doctor" and getattr(args, "component", None):
            state = host.components.get(args.component)
            payload = {
                "disclaimer": BOOTSTRAP_DISCLAIMER,
                "component": state.as_dict()
                if state
                else {"id": args.component, "state": "unknown"},
                "host": {"os": host.os, "architecture": host.architecture, "support": host.support},
            }
            text = f"{args.component}: {(state.state if state else 'unknown')}"
            return _emit(payload, json_mode=json_mode, text=text)
        payload = host.as_dict()
        payload["disclaimer"] = BOOTSTRAP_DISCLAIMER
        code = EXIT_CODES["ok"]
        if host.support in {"unsupported", "deferred"}:
            code = EXIT_CODES["unsupported"]
        _emit(payload, json_mode=json_mode, text=render_host(host))
        return code
    if command in {"bootstrap", "install", "repair", "update"}:
        plan_only = bool(getattr(args, "plan", False) or getattr(args, "dry_run", False))
        if command == "bootstrap" and getattr(args, "bootstrap_command", None) == "plan":
            plan_only = True
        if command == "bootstrap" and getattr(args, "bootstrap_command", None) == "apply":
            args.yes = True
        default_profile = None if getattr(args, "components", None) else "core"
        if (
            command == "bootstrap"
            and not getattr(args, "profile", None)
            and not getattr(args, "components", None)
            and sys.stdin.isatty()
            and sys.stdout.isatty()
            and not json_mode
            and not plan_only
        ):
            family, host = _load(getattr(args, "workspace", None))
            args.profile = _interactive_profile(host)
        family, host, plan = _plan_from_args(args, default_profile=default_profile)
        if plan_only or (command == "update" and not getattr(args, "yes", False)):
            payload = plan.as_dict()
            code = _exit_for_plan(plan)
            _emit(payload, json_mode=json_mode, text=render_plan(plan))
            return code
        executor = Executor(layout=layout_for(getattr(args, "workspace", None)))
        receipt = executor.execute(
            family,
            host,
            plan,
            dry_run=bool(getattr(args, "dry_run", False)),
            yes=bool(getattr(args, "yes", False)),
            interactive=sys.stdin.isatty() and sys.stdout.isatty() and not json_mode,
        )
        code = EXIT_CODES["ok"]
        if receipt.get("outcome") == "failed":
            code = EXIT_CODES["execution_failed"]
        elif receipt.get("outcome") == "partial":
            code = EXIT_CODES["incomplete"]
        _emit(receipt, json_mode=json_mode, text=render_receipt(receipt))
        return code
    if command == "configure":
        family, host, plan = _plan_from_args(args, default_profile=None)
        remaining = [
            action.as_dict()
            for action in plan.actions
            if action.kind in {"operator", "configure", "enable_service"}
        ]
        payload = {"disclaimer": BOOTSTRAP_DISCLAIMER, "actions": remaining}
        text = (
            "\n".join(item["summary"] for item in remaining)
            or "No remaining operator actions in the current plan."
        )
        return _emit(payload, json_mode=json_mode, text=text)
    if command == "deploy":
        args.profile = "worker"
        family, host, plan = _plan_from_args(args, default_profile="worker")
        payload = plan.as_dict()
        payload["notes"] = [
            "Bootstrap does not implement a shadow Fabric controller.",
            "Worker enrollment and rendezvous remain Fabric-owned operator operations.",
            "See mncs-fabric/deploy/systemd/WORKER_INSTALL.md.",
        ]
        if (
            getattr(args, "plan", False)
            or getattr(args, "dry_run", False)
            or not getattr(args, "yes", False)
        ):
            return _emit(
                payload,
                json_mode=json_mode,
                text=render_plan(plan) + "\n\n" + "\n".join(payload["notes"]),
            )
        executor = Executor(layout=layout_for(getattr(args, "workspace", None)))
        receipt = executor.execute(
            family,
            host,
            plan,
            dry_run=bool(getattr(args, "dry_run", False)),
            yes=True,
            interactive=False,
        )
        return _emit(receipt, json_mode=json_mode, text=render_receipt(receipt))
    if command == "uninstall":
        family = load_family()
        component = family.component(args.component_id)
        payload = {
            "disclaimer": BOOTSTRAP_DISCLAIMER,
            "component": component.id,
            "safe": False,
            "reason": (
                "Automated uninstall is limited: bootstrap will not delete operator "
                "ledgers, certificates, Commons stores, or service state. Remove the "
                "checkout and user services only with an explicit operator procedure "
                "from the owning repository."
            ),
            "owning_repository": component.repository.url,
        }
        if getattr(args, "yes", False) and not getattr(args, "dry_run", False):
            raise BootstrapError(
                "refusing destructive uninstall; use the owning repository procedure",
                exit_code=EXIT_CODES["privilege"],
            )
        return _emit(payload, json_mode=json_mode, text=payload["reason"])
    raise BootstrapError(f"unhandled bootstrap command: {command}")


def bootstrap_commands() -> frozenset[str]:
    return frozenset(COMMANDS)
