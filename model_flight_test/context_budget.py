"""Context-window budgeting helpers for accumulating qualification sessions.

The helpers in this module deliberately operate before transport.  A server's
context-limit rejection is valid behavior and must not be counted as a model or
serving failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence


Message = Dict[str, Any]
TokenCounter = Callable[[Sequence[Message]], int]


class ContextBudgetError(ValueError):
    """The newest indivisible conversation group cannot fit the input budget."""


@dataclass(frozen=True)
class ContextBudget:
    """A server context limit split into input, output, and safety headroom."""

    context_limit: int
    output_reserve: int = 4096
    safety_margin: int = 1024

    def __post_init__(self) -> None:
        if self.context_limit <= 0:
            raise ValueError("context_limit must be positive")
        if self.output_reserve <= 0:
            raise ValueError("output_reserve must be positive")
        if self.safety_margin < 0:
            raise ValueError("safety_margin cannot be negative")
        if self.input_limit <= 0:
            raise ValueError("output reserve and safety margin exhaust the context window")

    @property
    def input_limit(self) -> int:
        return self.context_limit - self.output_reserve - self.safety_margin

    def output_cap(self, input_tokens: int, requested: Optional[int] = None) -> int:
        """Return a valid output cap after reserving the safety margin."""

        available = self.context_limit - self.safety_margin - input_tokens
        if available <= 0:
            raise ContextBudgetError(
                f"input uses {input_tokens} tokens; no safe output budget remains"
            )
        return min(requested or self.output_reserve, available)


@dataclass(frozen=True)
class CompactionResult:
    messages: List[Message]
    input_tokens: int
    removed_groups: int

    @property
    def compacted(self) -> bool:
        return self.removed_groups > 0


def _copy_messages(messages: Iterable[Message]) -> List[Message]:
    return [dict(message) for message in messages]


def _split_conversation(messages: Sequence[Message]) -> tuple[List[Message], List[List[Message]]]:
    """Split a chat into a fixed prefix and complete user-led turn groups.

    Tool results remain attached to the assistant tool call that preceded them,
    because removal happens only at the next user-message boundary.
    """

    prefix: List[Message] = []
    groups: List[List[Message]] = []
    current: Optional[List[Message]] = None

    for message in _copy_messages(messages):
        if message.get("role") == "user":
            current = [message]
            groups.append(current)
        elif current is None:
            prefix.append(message)
        else:
            current.append(message)
    return prefix, groups


def compact_messages(
    messages: Sequence[Message],
    count_tokens: TokenCounter,
    budget: ContextBudget,
    *,
    checkpoint: Optional[str] = None,
    minimum_recent_groups: int = 1,
) -> CompactionResult:
    """Remove oldest complete turns until the next request fits.

    ``count_tokens`` must count the rendered chat template and any tool-schema
    tokens used by the caller.  ``checkpoint`` is a caller-produced compact
    state snapshot; this module never asks another model to summarize evidence.
    """

    if minimum_recent_groups < 1:
        raise ValueError("minimum_recent_groups must be at least one")

    prefix, groups = _split_conversation(messages)
    if not groups:
        input_tokens = count_tokens(prefix)
        if input_tokens > budget.input_limit:
            raise ContextBudgetError(
                f"fixed prompt uses {input_tokens} tokens; limit is {budget.input_limit}"
            )
        return CompactionResult(prefix, input_tokens, 0)

    checkpoint_message = (
        [{"role": "system", "content": checkpoint}] if checkpoint else []
    )
    removed = 0

    while True:
        candidate = prefix + (checkpoint_message if removed else [])
        candidate += [message for group in groups[removed:] for message in group]
        input_tokens = count_tokens(candidate)
        if input_tokens <= budget.input_limit:
            return CompactionResult(candidate, input_tokens, removed)
        if len(groups) - removed <= minimum_recent_groups:
            raise ContextBudgetError(
                "newest conversation group cannot fit the safe input budget: "
                f"{input_tokens} > {budget.input_limit}"
            )
        removed += 1


def is_context_limit_error(http_status: Optional[int], body: Any) -> bool:
    """Recognize an OpenAI-compatible deterministic context-budget rejection."""

    if http_status != 400:
        return False
    text = str(body or "").lower()
    explicit_markers = (
        "maximum context length",
        "context length is",
        "context_length_exceeded",
    )
    return any(marker in text for marker in explicit_markers) or (
        "input_tokens" in text and "context" in text and "exceed" in text
    )


def classify_request_error(http_status: Optional[int], body: Any) -> str:
    """Keep invalid test construction separate from serving failures."""

    if is_context_limit_error(http_status, body):
        return "harness-invalid"
    return "serving-failure"
