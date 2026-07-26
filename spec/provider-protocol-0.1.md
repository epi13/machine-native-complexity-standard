# MNCS Provider Protocol 0.1

Provider Protocol 0.1 is deterministic JSON Lines over stdin/stdout. One request
produces one response. Every message includes `protocol_version: "0.1"`, a type, a
provider or request identity as applicable, and extensions.

Requests are capabilities, analysis_request, health, or cancel. Responses are
capabilities, analysis_response, health_response, cancelled, or error. Analysis status
is exactly PASS, FAIL, or UNKNOWN; unsupported and bounded-out analysis returns UNKNOWN
or a structured error, never PASS. Witnesses are compact JSON and MUST NOT require
execution to inspect.

Validation does not launch providers. Explicit launch uses an argument array without a
shell, dedicated workspace, timeout, output caps, strict stdout framing, and descendant
termination. This protocol does not itself provide network isolation.
