# Provider adapter contract

The public skill should depend on a small adapter rather than a specific
deployment. An adapter supplies:

- `list_models()` with exact model ID and enforced context limit;
- `chat(messages, model, tools, generation)` returning raw response, model ID,
  finish reason, usage, latency, and tool calls;
- `read_only_status()` for endpoint/runtime evidence;
- `read_only_version()` when the provider exposes a runtime version;
- `capture_serving_config()` for process, image, cache, batching, topology, and
  speculative-decoding evidence.

The adapter must not silently fall back, mutate the service, publish messages,
or write outside the caller-provided run directory. Provider-specific SSH,
cluster commands, credentials, and hostnames belong in adapter implementations
or private deployment repositories, never in the portable skill contract.
