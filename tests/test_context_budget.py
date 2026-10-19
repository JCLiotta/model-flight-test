import unittest

from model_flight_test.context_budget import (
    ContextBudget,
    ContextBudgetError,
    classify_request_error,
    compact_messages,
)


def synthetic_counter(messages):
    return sum(int(message.get("tokens", 0)) for message in messages)


class ContextBudgetTests(unittest.TestCase):
    def test_exact_one_token_over_is_rejected_before_transport(self):
        budget = ContextBudget(262_144, output_reserve=16_384, safety_margin=0)
        messages = [
            {"role": "system", "content": "system", "tokens": 1},
            {"role": "user", "content": "oversized", "tokens": 245_760},
        ]

        with self.assertRaisesRegex(ContextBudgetError, "245761 > 245760"):
            compact_messages(messages, synthetic_counter, budget)

    def test_oldest_complete_group_is_removed_with_tool_pair_intact(self):
        budget = ContextBudget(100, output_reserve=20, safety_margin=10)
        messages = [
            {"role": "system", "content": "system", "tokens": 10},
            {"role": "user", "content": "old", "tokens": 20},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call-1"}],
                "tokens": 15,
            },
            {"role": "tool", "tool_call_id": "call-1", "content": "result", "tokens": 15},
            {"role": "assistant", "content": "old answer", "tokens": 10},
            {"role": "user", "content": "new", "tokens": 20},
            {"role": "assistant", "content": "new answer", "tokens": 10},
        ]

        result = compact_messages(
            messages,
            synthetic_counter,
            budget,
            checkpoint="state",
        )

        self.assertEqual(result.removed_groups, 1)
        self.assertEqual(result.input_tokens, 40)
        self.assertEqual([message["role"] for message in result.messages], ["system", "system", "user", "assistant"])
        self.assertNotIn("call-1", repr(result.messages))

    def test_output_cap_keeps_total_below_window(self):
        budget = ContextBudget(262_144, output_reserve=16_384, safety_margin=1_024)
        cap = budget.output_cap(245_000)
        self.assertEqual(cap, 16_120)
        self.assertLessEqual(245_000 + cap + budget.safety_margin, budget.context_limit)

    def test_context_http_400_is_harness_invalid(self):
        body = {
            "error": {
                "message": "maximum context length is 262144; input_tokens exceeded",
                "code": 400,
            }
        }
        self.assertEqual(classify_request_error(400, body), "harness-invalid")
        self.assertEqual(classify_request_error(503, body), "serving-failure")


if __name__ == "__main__":
    unittest.main()
