# Deterministic flight suite v1

The target model must not see validator notes.

## FT-01 — Exact instruction and format

Ask for exactly one minified JSON object with ordered keys `status`, `values`,
and `note`; require `status: "ok"`, squares of 3, 5, and 7, and a six-letter
lowercase ASCII note without `e`.

Pass only when the output is valid minified JSON, key order and values are
correct, and the note matches `^[a-df-z]{6}$`. Extra prose is a failure.

## FT-02 — Reasoning and uncertainty

Use the two-box red/blue-ball problem: observing a red ball favors the
two-red composition, but no unique posterior is justified without a prior.
Require exactly two lines, `ANSWER:` and `WHY:`. A fabricated numeric posterior
fails.

## FT-03 — Code and edge cases

Request a Python `parse_port(value)` function accepting integers or unpadded
decimal strings from 1 through 65535 and rejecting booleans, whitespace,
signs, decimals, empty strings, zero, and out-of-range values with
`ValueError`. Extract and execute in a disposable directory with network
disabled. Add hidden checks for every named rejection class and require at
least eight meaningful supplied assertions.

## FT-04 — Single tool use

Require exactly one read-only session-status call, then exactly
`MODEL=<provider/model>` from its result. No guessing or extra tool calls.

## FT-05 — Sequential tools

In one fresh isolated session, require session status followed by a read-only
version command, then exactly two lines containing the values from those tool
results. Validate call order, arguments, and trace evidence.

## FT-06 — Safe-failure recovery

Provide a unique nonexistent disposable path. Require one read attempt, no
creation/search/retry, diagnosis from the error, and exactly
`RECOVERED=missing-file`.

## Record schema

Each result records the suite version, test ID, status (`pass`, `partial`,
`fail`, or `not_tested`), failure class, timestamps, latency, TTFT and
tokens/second when directly exposed, exact prompt, response, tool trace, and
validator evidence. Missing evidence is `null`, never an inferred pass.
