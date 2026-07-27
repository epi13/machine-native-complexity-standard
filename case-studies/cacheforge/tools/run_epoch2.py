from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "machine"))

from cacheforge.epoch2 import evaluate_epoch2  # noqa: E402
from generated_policy import GeneratedEvictionPolicy  # noqa: E402

OUTPUT = ROOT / "evidence" / "results" / "epoch-2-development.json"


def main() -> int:
    summary = evaluate_epoch2(GeneratedEvictionPolicy)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "development_result": summary["development_result"],
                "formal_mncs_status": summary["formal_mncs_status"],
                "output": str(OUTPUT),
            },
            sort_keys=True,
        )
    )
    return 0 if summary["development_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
