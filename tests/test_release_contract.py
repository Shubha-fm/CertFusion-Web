"""Independent executable contract tests for verification-status release logic.

These tests check the decision policy, not the MRI model, SMT solver,
TLC execution, or end-to-end production application.
Run: python -m unittest discover -s tests -p 'test_release_contract.py' -v
"""
import unittest

def decide_release(solver_outcome, prediction_present, provenance_present):
    """A conservative reference policy for research-report status."""
    if solver_outcome not in {"UNSAT", "SAT", "TIMEOUT", "NOT_RUN"}:
        raise ValueError("Unknown solver outcome")
    if not prediction_present:
        return "INCOMPLETE"
    if not provenance_present:
        return "INCOMPLETE"
    if solver_outcome == "UNSAT":
        return "PROPERTY_VERIFIED"
    if solver_outcome == "SAT":
        return "PROPERTY_VIOLATED_OR_ABSTRACT_COUNTEREXAMPLE"
    if solver_outcome == "TIMEOUT":
        return "UNRESOLVED"
    return "NOT_VERIFIED"

class ReleaseContractTests(unittest.TestCase):
    def test_unsat_requires_prediction_and_provenance(self):
        self.assertEqual(decide_release("UNSAT", True, True), "PROPERTY_VERIFIED")
        self.assertNotEqual(decide_release("UNSAT", False, True), "PROPERTY_VERIFIED")
        self.assertNotEqual(decide_release("UNSAT", True, False), "PROPERTY_VERIFIED")

    def test_sat_never_promoted(self):
        self.assertEqual(decide_release("SAT", True, True), "PROPERTY_VIOLATED_OR_ABSTRACT_COUNTEREXAMPLE")

    def test_timeout_never_promoted(self):
        self.assertEqual(decide_release("TIMEOUT", True, True), "UNRESOLVED")

    def test_not_run_never_promoted(self):
        self.assertEqual(decide_release("NOT_RUN", True, True), "NOT_VERIFIED")

    def test_missing_provenance_blocks_release(self):
        for outcome in ("UNSAT", "SAT", "TIMEOUT", "NOT_RUN"):
            self.assertEqual(decide_release(outcome, True, False), "INCOMPLETE")

    def test_bad_solver_value_is_rejected(self):
        with self.assertRaises(ValueError):
            decide_release("SUCCESS", True, True)

if __name__ == "__main__":
    unittest.main()
