"""Optional real Pulumi CLI/provider test against an isolated fake service."""

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

from contract import classify_claim, load_scenarios  # noqa: E402
from pulumi_loopback_adapter import PulumiLoopbackAdapter, _fixture_env  # noqa: E402


class PulumiLoopbackAdapterTest(unittest.TestCase):
    def test_fixture_environment_refuses_remote_hosts_and_excludes_inherited_secrets(self):
        for url in ("https://api.redislabs.com/v1", "http://localhost:1234/v1", "http://127.0.0.1:1234/other", "http://user:password@127.0.0.1:1234/v1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _fixture_env("/tmp/fixture", url)
        with patch.dict(os.environ, {"REDISCLOUD_QA": "credential-sentinel", "REDISCLOUD_SECRET_KEY": "secret-sentinel", "AWS_SECRET_ACCESS_KEY": "cloud-sentinel"}):
            env = _fixture_env("/tmp/fixture", "http://127.0.0.1:1234/v1")
        self.assertNotIn("REDISCLOUD_QA", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertEqual(env["REDISCLOUD_SECRET_KEY"], "fake")
        self.assertNotIn("secret-sentinel", env.values())

    @unittest.skipUnless(os.environ.get("PULUMI_LOOPBACK_PROVIDER"), "provider fixture not built")
    def test_real_provider_against_loopback_only(self):
        scenarios = load_scenarios(CONTRACT_DIR / "scenarios.json")
        scenario = scenarios["essentials-database-lifecycle"]
        adapter = PulumiLoopbackAdapter(os.environ.get("PULUMI_LOOPBACK_CLI", "pulumi"), os.environ["PULUMI_LOOPBACK_PROVIDER"])
        result = adapter.execute(scenario)
        self.assertEqual(result.outcome, "blocked")
        self.assertEqual(result.mode, "simulated")
        self.assertEqual(classify_claim(scenario, result), "blocked")
        self.assertEqual(result.steps[0].outcome, "blocked")
        self.assertTrue(all(item.outcome == "passed" for item in result.steps[1:]))
        self.assertEqual(result.cleanup, "clean")
        self.assertNotEqual(classify_claim(scenario, replace(result, mode="live")), "live_claim_requires_verification")
        self.assertEqual(result.evidence_url, "https://fixture.invalid/log")
        update = adapter.execute(scenarios["essentials-database-eviction-update"])
        self.assertEqual(update.outcome, "unsupported")
        self.assertEqual(update.mode, "simulated")


if __name__ == "__main__":
    unittest.main()
