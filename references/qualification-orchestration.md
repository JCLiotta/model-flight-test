# Long qualification orchestration

Use this reference for soak, qualification, or multi-phase evaluation.

## Preflight

Create a new run directory and sentinel. Run fixture and validator self-tests,
including JSON number-versus-string and exact-key-order cases. Verify every
writer and reporter uses the new root and that known-good and known-bad
artifact-shape fixtures behave as expected. Capture the live serving process,
not just a historical recipe.

## Workload

After the six-test flight, exercise a context ladder with a safety margin below
the advertised limit, then nonce/session-isolation probes, four concurrent
lanes of 40 turns, safe-failure recovery, and final post-tool replay. Stop a
lane at its target; a wall-clock ceiling is only a safety bound. If the ceiling
arrives first, the phase is incomplete.

Every lane must isolate exceptions and convert invalid tool arguments or
sandbox errors into structured tool results. A lane exception must not crash
aggregation or erase completed lane evidence.

## Attribution and recovery

Keep these distinct:

- `harness-invalid`: the request budget or fixture was invalid;
- `model-failure`: the response violated the task or validator;
- `serving-failure`: timeout, substitution, null/empty output, repeated/filler
  output, malformed tool syntax, fabricated tool evidence, or truncation;
- `harness-failure`: the runner, path contract, or phase writer malfunctioned;
- `reporter-failure`: final aggregation failed after valid phase artifacts.

If reporting fails after complete phase artifacts exist, repair or rerun only
the reporter with a finalize-only path. Never rerun inference or upgrade the
model result merely because reporting was repaired.

## Completion

Audit the final report against authoritative phase artifacts: target counters,
canaries, validators, errors, timeouts, substitutions, corruption signatures,
invalid requests, elapsed time, and final status must agree. Report serving
stability separately from qualification compliance.
