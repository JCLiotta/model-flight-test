# Model Flight Test

Deterministic qualification for language-model serving and agent workloads.
The project separates model behavior from serving, harness, and reporter
failures. It is suitable for OpenAI-compatible local endpoints and can be
extended with provider adapters without embedding deployment-specific hosts or
credentials.

## Included

- AgentSkill entrypoint in `SKILL.md`.
- Six deterministic flight-test definitions and mechanical verdict gates.
- Dependency-free validators for exact format, uncertainty, code, and recovery.
- JSON Schemas for individual results and atomic progress status.
- Provider adapter contract and a standard-library OpenAI-compatible client.
- Unit tests and private-data exclusion guidance.

## Repository layout

```text
model-flight-test/
├── SKILL.md
├── README.md
├── LICENSE
├── pyproject.toml
├── model_flight_test/
│   └── validators.py
├── scripts/
│   └── validate_records.py
├── references/
│   ├── suite-v1.md
│   ├── qualification-orchestration.md
│   └── provider-adapter-contract.md
├── schemas/
│   ├── result.schema.json
│   └── status.schema.json
├── adapters/
│   └── openai_compatible/
└── tests/
    ├── validator-fixtures/
    └── smoke/
```

## Quick start

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_records.py records.json
```

`validate_records.py` grades captured responses locally. It never calls a
model, uses another model as a judge, or treats self-reported success as
evidence.

## Qualification rules

The long qualification uses four isolated concurrent 40-turn lanes, a
high-context ladder, nonce isolation, safe-failure recovery, and final replay.
It reports the six-test verdict, serving stability, and qualification
compliance separately. Read the linked references before implementing a full
runner.

Provider adapters must not silently fall back, mutate a service, publish
messages, or write outside the caller-provided run directory.
