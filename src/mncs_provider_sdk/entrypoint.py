"""One-request provider entrypoint with stable error framing."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

from .framing import read_message, write_message
from .models import Capabilities, ProviderError, ProviderIdentity

Handler = Callable[[dict[str, Any]], dict[str, Any]]


def provider_main(identity: ProviderIdentity, capabilities: Capabilities, handler: Handler) -> int:
    try:
        request = read_message(sys.stdin)
        request_type = request.get("type")
        if request.get("protocol_version") != "0.1":
            raise ValueError("unsupported protocol version")
        if request_type == "capabilities":
            response = capabilities.as_dict()
        elif request_type == "health":
            response = {
                "protocol_version": "0.1",
                "type": "health_response",
                "provider": identity.__dict__,
                "status": "PASS",
                "extensions": {},
            }
        elif request_type == "cancel":
            response = {
                "protocol_version": "0.1",
                "type": "cancelled",
                "provider": identity.__dict__,
                "request_id": request.get("request_id", ""),
                "extensions": {},
            }
        elif request_type == "analysis_request":
            response = handler(request)
        else:
            raise ValueError("unsupported request")
    except (KeyError, TypeError, ValueError) as exc:
        response = ProviderError(
            "",
            identity,
            "invalid_request",
            str(exc),
        ).as_dict()
    write_message(sys.stdout, response)
    return 0
