"""Run only with the exact provisional shared contract, with no credentials."""

import hashlib
from dataclasses import replace
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

CONTRACT_DIR = Path(os.environ["ACCEPTANCE_CONTRACT_DIR"])
EXPECTED = {
    "contract.py": "ea4e814af164658654dc860bad4c9549526d347793e25856a0e2afba794236c0",
    "scenarios.json": "66f926d8c9a26acb6b2952b68280a1f82e71e98d2f463ff32862505b3989865a",
}
for name, digest in EXPECTED.items():
    if hashlib.sha256((CONTRACT_DIR / name).read_bytes()).hexdigest() != digest:
        raise RuntimeError("provisional shared contract content does not match the pinned revision")
sys.path.insert(0, str(CONTRACT_DIR))

from contract import Scenario, classify_claim, load_scenarios  # noqa: E402
from pulumi_simulated_adapter import SimulatedPulumiAdapter  # noqa: E402
import pulumi_simulated_adapter  # noqa: E402


class PulumiSharedScenarioTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_scenarios(CONTRACT_DIR / "scenarios.json")
        self.adapter = SimulatedPulumiAdapter()

    def test_lifecycle_runs_simulated_shared_scenario(self):
        scenario = self.cases["essentials-database-lifecycle"]
        result = self.adapter.execute(scenario)
        self.assertEqual(result.provider, "pulumi")
        self.assertEqual(result.mode, "simulated")
        self.assertEqual(classify_claim(scenario, result), "simulated_claim_requires_verification")
        self.assertEqual(classify_claim(scenario, replace(result, mode="live")), "invalid")
        self.assertEqual(result.run_url, "https://fixture.invalid/run")
        self.assertEqual(result.evidence_url, "https://fixture.invalid/log")
        self.assertEqual(result.source_revision, "0" * 40)
        self.assertTrue(all(item.evidence_url.startswith("https://fixture.invalid/") for item in result.steps))

    def test_update_is_explicitly_unsupported(self):
        scenario = self.cases["essentials-database-eviction-update"]
        result = self.adapter.execute(scenario)
        self.assertEqual(result.mode, "simulated")
        self.assertEqual(result.outcome, "unsupported")
        self.assertEqual(classify_claim(scenario, result), "unsupported")

    def test_changed_lifecycle_contract_blocks(self):
        original = self.cases["essentials-database-lifecycle"]
        changed = Scenario(original.id, original.steps[:-1])
        result = self.adapter.execute(changed)
        self.assertEqual(result.mode, "simulated")
        self.assertEqual(result.outcome, "blocked")
        self.assertEqual(result.cleanup, "not_started")

    def test_simulated_failed_lock_cannot_report_pass(self):
        backend = pulumi_simulated_adapter.FakeBackend()
        backend.locked = False
        with patch.object(pulumi_simulated_adapter, "FakeBackend", return_value=backend):
            result = self.adapter.execute(self.cases["essentials-database-lifecycle"])
        self.assertEqual(result.mode, "simulated")
        self.assertEqual(result.outcome, "fail")
        self.assertEqual(result.cleanup, "unknown")
        self.assertNotIn("create subscription", backend.events)


if __name__ == "__main__":
    unittest.main()
