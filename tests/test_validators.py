import unittest

from model_flight_test.validators import validate_flight_test


class ValidatorTests(unittest.TestCase):
    def test_exact_json(self):
        self.assertEqual(
            validate_flight_test("FT-01", '{"status":"ok","values":[9,25,49],"note":"abcdfg"}')['status'],
            "pass",
        )

    def test_uncertainty_accepts_equivalent_wording(self):
        text = ("ANSWER: The red draw supports the 2-red/1-blue box with likelihood ratio 2:1, "
                "but no posterior probability is determined without a prior.\n"
                "WHY: The likelihoods are 2/3 and 1/3, while prior odds are unspecified.")
        self.assertEqual(validate_flight_test("FT-02", text)["status"], "pass")

    def test_uncertainty_rejects_claimed_posterior(self):
        text = "ANSWER: posterior is 2/3\nWHY: prior was assumed"
        self.assertEqual(validate_flight_test("FT-02", text)["status"], "fail")

    def test_port_parser_with_eight_asserts(self):
        text = '''```python
def parse_port(value):
    if isinstance(value, bool): raise ValueError()
    if isinstance(value, int) and 1 <= value <= 65535: return value
    if isinstance(value, str) and value.isdigit() and 1 <= int(value) <= 65535: return int(value)
    raise ValueError()
assert parse_port(1) == 1
assert parse_port(2) == 2
assert parse_port(3) == 3
assert parse_port(4) == 4
assert parse_port(5) == 5
assert parse_port(6) == 6
assert parse_port(7) == 7
assert parse_port(8) == 8
```'''
        self.assertEqual(validate_flight_test("FT-03", text)["status"], "pass")

    def test_safe_recovery(self):
        self.assertEqual(
            validate_flight_test("FT-06", "RECOVERED=missing-file", [{"tool": "exec", "ok": False}])["status"],
            "pass",
        )


if __name__ == "__main__":
    unittest.main()
