---
name: model-flight-test
description: Qualify a named local or remote language model with deterministic format, reasoning, coding, tool-use, recovery, long-context, concurrency, and artifact-integrity tests. Use when a user asks to evaluate, soak, benchmark for agent use, or compare a serving target; do not use for ordinary single-prompt model comparisons.
metadata:
  short-description: Run evidence-based model qualification
---

# Model flight test

Run a reproducible model qualification against an explicitly named model or
endpoint. The result is evidence, not a subjective model review: preserve
the exact requests, responses, tool traces, measured timings, validator
versions, serving configuration, and artifact paths.

## Required behavior

- Pin every request to the target provider/model and verify the returned model
  identifier. A fallback, substitution, or unidentifiable target invalidates
  the run.
- Use fresh isolated sessions for independent tests. Share a session only when
  measuring retained context or multi-turn state.
- Grade with deterministic validators and tool traces. Never use another model
  as a subjective judge and never accept the target's self-reported success.
- Keep test tools read-only or confined to a disposable run directory. Do not
  send messages, publish results, change live services, or spend money as part
  of a flight test unless the user separately authorizes that action.
- Create a new timestamped run directory with a sentinel before inference.
  Prove that prompts, fixtures, responses, traces, status, and reports resolve
  beneath it; reject fallback paths that point at older runs.
- Record serving configuration before inference: model revision, runtime/image,
  context limit, batching, cache settings, speculative decoding, quantization,
  topology, and relevant generation settings.
- Budget every context probe as input tokens plus reserved output tokens plus
  required protocol headroom. A correctly rejected over-budget request is
  `harness-invalid`, not serving instability.
- Update an atomic machine-readable status file after every meaningful batch.
  Report observed counters; do not infer progress from elapsed time or model
  prose.

## Test modes

For a normal flight, read [suite-v1.md](references/suite-v1.md) and run all six
tests in order. For a soak or qualification, read both
[suite-v1.md](references/suite-v1.md) and
[qualification-orchestration.md](references/qualification-orchestration.md),
then run the six-test flight, context ladder, nonce isolation, concurrent
lanes, safe-failure recovery, and final replay.

The default long qualification has four concurrent 40-turn lanes:

- coding and verification;
- long-context evidence synthesis;
- stateful planning under revisions;
- tool failures and recovery.

Use exact-format canaries at a fixed cadence, normally every tenth turn, but
make each canary compatible with that lane's output schema. Keep canary misses,
validator failures, request errors, serving corruption, harness defects, and
reporter failures as separate categories.

## Verdicts

For the six-test flight, return exactly one of: `Agent-ready`, `Assistant-only`,
`Disposable utility`, or `Grounded`. Apply the gates in the suite reference;
never upgrade a partial result to a pass.

For a long qualification, report these independently:

1. the six-test flight verdict;
2. serving stability;
3. qualification compliance.

Missing targets, validators, recovery/replay, configuration proof, or final
artifacts prevents qualification. Clean serving does not compensate for a
failed strict-format or compliance gate.

## Deliverables

Write `report.md`, `results.json`, a run manifest, status, exact prompts,
responses, tool traces, metrics, and bounded serving logs under the run
directory. The report must cite the matched gate, decisive evidence, elapsed
time, measured metrics, incomplete targets, and artifact paths. Do not paste
long raw outputs into chat.
