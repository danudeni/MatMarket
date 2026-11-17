import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import rules, segments, truth_table  # noqa: E402
from logic.parser import ExpressionError, evaluate, parse  # noqa: E402


class LogicTests(unittest.TestCase):
    def test_precedence(self):
        self.assertTrue(evaluate(parse("a OR b AND c"), {"a": True}))
        self.assertFalse(evaluate(parse("(a OR b) AND c"), {"a": True}))

    def test_implication(self):
        self.assertFalse(evaluate(parse("p -> q"), {"p": True, "q": False}))
        self.assertTrue(evaluate(parse("p -> q"), {"p": False, "q": False}))

    def test_tautology_and_contradiction(self):
        self.assertIn("Tautologi", truth_table.build("p OR NOT p")["kind"])
        self.assertIn("Kontradiksi", truth_table.build("p AND NOT p")["kind"])

    def test_contrapositive_equivalence(self):
        self.assertTrue(truth_table.equivalent("p -> q", "~q -> ~p"))
        self.assertFalse(truth_table.equivalent("p -> q", "q -> p"))

    def test_invalid(self):
        for bad in ["", "p AND", "(p OR q", "p $ q"]:
            with self.assertRaises(ExpressionError):
                parse(bad)

    def test_rules(self):
        rs = [{"name": "r", "condition": "a AND NOT b", "strategy": "s", "kind": "strategi", "priority": 1}]
        self.assertEqual(rules.fact_variables(rs), ["a", "b"])
        hit, miss = rules.evaluate_rules(rs, {"a": True, "b": False})
        self.assertEqual((len(hit), len(miss)), (1, 0))

    def test_segments(self):
        data = {"A": {"x", "y"}, "B": {"y", "z"}}
        out = segments.analyze(data, "A AND NOT B")
        self.assertEqual(out["result"]["members"], ["x"])


if __name__ == "__main__":
    unittest.main()
