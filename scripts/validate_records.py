#!/usr/bin/env python3
"""Validate captured flight-test records with deterministic local validators."""

import argparse
import json
from pathlib import Path

from model_flight_test.validators import validate_flight_test


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records", type=Path, help="JSON list of captured test records")
    args = parser.parse_args()
    records = json.loads(args.records.read_text())
    if not isinstance(records, list):
        raise SystemExit("records must be a JSON array")
    failures = 0
    for record in records:
        result = validate_flight_test(record["test_id"], record.get("response", ""), record.get("tool_trace", []))
        print(f"{record['test_id']}: {result['status']} — {result['evidence']}")
        if result["status"] in {"fail", "not_tested"}:
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
