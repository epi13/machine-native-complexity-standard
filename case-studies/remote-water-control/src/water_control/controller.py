# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Any

from water_control.journal import IntentJournal
from water_control.model import (
    AuthorizedIntent,
    ControllerState,
    SystemConfig,
    TelemetrySample,
)
from water_control.planner import Planner
from water_control.safety import SafetyKernel


class Controller:
    def __init__(
        self,
        planner: Planner,
        config: SystemConfig | None = None,
        *,
        state: ControllerState | None = None,
        journal: IntentJournal | None = None,
    ) -> None:
        self.planner = planner
        self.config = config or SystemConfig()
        self.state = state or ControllerState()
        self.journal = journal or IntentJournal(last_sequence=self.state.last_sequence)
        self.safety = SafetyKernel(self.config)

    def decide(self, sample: TelemetrySample, now_s: int) -> AuthorizedIntent:
        proposal = self.planner.propose(sample, self.state, self.config)
        adjudication = self.safety.authorize(proposal, sample, self.state, now_s)
        sequence = self.state.last_sequence + 1
        intent = AuthorizedIntent(
            sequence=sequence,
            issued_at_s=now_s,
            expires_at_s=now_s + self.config.intent_ttl_s,
            duty_on=adjudication.duty_on,
            standby_on=adjudication.standby_on,
            mode=adjudication.mode,
            planner_id=proposal.planner_id,
            proposal_reason=proposal.reason,
            safety_reasons=adjudication.reasons,
        )
        self.journal.append(intent)
        self._apply_intent(intent)
        return intent

    def _apply_intent(self, intent: AuthorizedIntent) -> None:
        if intent.duty_on != self.state.duty_on:
            self.state.duty_last_changed_s = intent.issued_at_s
        if intent.standby_on != self.state.standby_on:
            self.state.standby_last_changed_s = intent.issued_at_s
        self.state.duty_on = intent.duty_on
        self.state.standby_on = intent.standby_on
        self.state.last_sequence = intent.sequence
        self.state.last_mode = intent.mode

    def checkpoint_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "0.1",
            "planner_id": self.planner.planner_id,
            "controller_state": self.state.as_dict(),
            "journal": self.journal.snapshot(),
        }

    @classmethod
    def restore(
        cls,
        planner: Planner,
        payload: dict[str, Any],
        config: SystemConfig | None = None,
    ) -> Controller:
        if payload.get("planner_id") != planner.planner_id:
            raise ValueError("checkpoint planner identity mismatch")
        state = ControllerState.from_dict(payload["controller_state"])
        journal_payload = payload["journal"]
        journal = IntentJournal(
            last_sequence=int(journal_payload["last_sequence"]),
            tail_hash=str(journal_payload["tail_hash"]),
        )
        if journal.last_sequence != state.last_sequence:
            raise ValueError("checkpoint sequence mismatch")
        return cls(planner, config, state=state, journal=journal)
