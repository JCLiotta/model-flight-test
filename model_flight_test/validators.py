"""Dependency-free validators for Flight Test Suite v1.

The validators grade captured model output. They do not call a model, choose a
judge model, or infer success from prose about an unrecorded tool trace.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


Result = Dict[str, Any]


def _result(status: str, evidence: str, **extra: Any) -> Result:
    return {"status": status, "evidence": evidence, **extra}


def validate_ft01(text: str) -> Result:
    try:
        value = json.loads(text.strip())
    except Exception as exc:
        return _result("fail", "invalid JSON", error=str(exc))
    issues: List[str] = []
    if list(value.keys()) != ["status", "values", "note"]:
        issues.append("key order/keys")
    if value.get("status") != "ok":
        issues.append("status")
    if value.get("values") != [9, 25, 49]:
        issues.append("values")
    if not re.fullmatch(r"[a-df-z]{6}", str(value.get("note", ""))):
        issues.append("note")
    return _result("pass" if not issues else "partial" if len(issues) == 1 else "fail",
                   "exact" if not issues else "invalid " + ", ".join(issues))


def validate_ft02(text: str) -> Result:
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    fmt_ok = len(lines) == 2 and lines[0].startswith("ANSWER:") and lines[1].startswith("WHY:")
    low = text.lower()
    no_posterior = any(term in low for term in (
        "no unique posterior", "posterior probability is indeterminate",
        "posterior probability is undetermined", "posterior.*cannot",
        "cannot be determined", "cannot be computed", "cannot be assigned",
        "without a prior", "prior.*unspecified", "prior odds.*unknown",
    ))
    favors = any(term in low for term in (
        "two red", "2 red", "two-red", "more likely", "supports the",
        "favors the", "favours the", "likelihood ratio",
    ))
    # A likelihood ratio is allowed; a claimed posterior fraction is not.
    claimed_posterior = re.search(r"posterior[^.\n]{0,50}\b(?:2/3|1/2|1/3|[0-9]+%)\b", low)
    if claimed_posterior:
        return _result("fail", "invented numeric posterior")
    if no_posterior and favors and fmt_ok:
        return _result("pass", "exact")
    if no_posterior and favors:
        return _result("partial", "correct conclusion, format issue")
    if no_posterior or favors:
        return _result("partial", "partial reasoning")
    return _result("fail", "wrong conclusion")


def _extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", text or "", re.S | re.I)
    return match.group(1) if match else text


def _port_hidden_checks(code: str) -> Tuple[bool, str]:
    checks = [
        ("1", 1), ("65535", 65535), ("'443'", 443),
        ("True", "raise"), ("' 80'", "raise"), ("'+80'", "raise"),
        ("'8.0'", "raise"), ("''", "raise"), ("0", "raise"),
        ("65536", "raise"),
    ]
    body = code + "\n"
    with tempfile.TemporaryDirectory(prefix="flight-test-ft03-") as directory:
        runner = Path(directory) / "runner.py"
        cases = []
        for literal, expected in checks:
            if expected == "raise":
                cases.append(
                    "try:\n"
                    f"    parse_port({literal})\n"
                    f"    results.append(('fail', {literal!r}))\n"
                    "except ValueError:\n"
                    f"    results.append(('ok', {literal!r}))\n"
                    "except Exception as exc:\n"
                    f"    results.append(('wrong', {literal!r}, type(exc).__name__))\n"
                )
            else:
                cases.append(
                    "try:\n"
                    f"    results.append(('ok', parse_port({literal}) == {expected!r}))\n"
                    "except Exception as exc:\n"
                    f"    results.append(('wrong', {literal!r}, type(exc).__name__))\n"
                )
        runner.write_text(body + "\nresults=[]\n" + "\n".join(cases) + "\nprint(results)\n")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(runner)], cwd=directory,
                capture_output=True, text=True, timeout=20,
                env={"PATH": "/usr/bin:/bin"},
            )
        except subprocess.TimeoutExpired:
            return False, "hidden checks timed out"
        if proc.returncode:
            return False, "hidden runner failed: " + proc.stderr[-300:]
        try:
            values = ast.literal_eval(proc.stdout.strip())
        except Exception:
            return False, "hidden runner returned unreadable results"
        if any(item[0] != "ok" or (len(item) > 1 and item[1] is False) for item in values):
            return False, "hidden checks failed"
    return True, "hidden checks pass"


def validate_ft03(text: str) -> Result:
    code = _extract_code(text)
    if not code.strip():
        return _result("fail", "no code")
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return _result("fail", "code does not parse", error=str(exc))
    hidden_ok, hidden_evidence = _port_hidden_checks(code)
    if not hidden_ok:
        return _result("fail", hidden_evidence)
    assert_count = len(re.findall(r"^\s*assert\b", code, re.M))
    if assert_count < 8:
        return _result("partial", f"{hidden_evidence}, only {assert_count} direct asserts")
    return _result("pass", f"{hidden_evidence}, {assert_count} direct asserts")


def validate_tool_test(test_id: str, final: str, trace: Iterable[Dict[str, Any]]) -> Result:
    calls = list(trace)
    if test_id == "FT-04":
        if len(calls) != 1 or calls[0].get("tool") != "session_status":
            return _result("fail", "tool trace is not exactly one session-status call")
        return _result("pass" if re.fullmatch(r"MODEL=\S+", final.strip()) else "partial",
                       "exact" if re.fullmatch(r"MODEL=\S+", final.strip()) else "format issue")
    if test_id == "FT-05":
        order = [item.get("tool") for item in calls]
        good = order[:2] == ["session_status", "exec"] and len(calls) == 2
        return _result("pass" if good and len(final.strip().splitlines()) == 2 else "partial" if good else "fail",
                       "exact" if good and len(final.strip().splitlines()) == 2 else "trace or format issue")
    if test_id == "FT-06":
        good = len(calls) == 1 and calls[0].get("ok") is False and final.strip() == "RECOVERED=missing-file"
        return _result("pass" if good else "fail", "exact recovery" if good else "unsafe or incomplete recovery")
    raise ValueError(f"unsupported tool test: {test_id}")


def validate_flight_test(test_id: str, text: str, trace: Iterable[Dict[str, Any]] = ()) -> Result:
    if test_id == "FT-01":
        return validate_ft01(text)
    if test_id == "FT-02":
        return validate_ft02(text)
    if test_id == "FT-03":
        return validate_ft03(text)
    return validate_tool_test(test_id, text, trace)
