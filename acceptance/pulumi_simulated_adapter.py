"""Provisional shared-contract adapter with a strictly in-memory backend.

This exercises the scenario interface and Python proof model only. It does not
run Pulumi, the generated SDK, a provider, Cloud, a real lock, or a journal.
There is no switch or input that can change its evidence mode to live.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from contract import Evidence, StepReceipt  # noqa: E402  -- pinned external provisional contract
from qa_essentials_fake import FakeBackend  # noqa: E402
from qa_essentials_model import ProofError, run_model  # noqa: E402


LIFECYCLE = (
    "admission_and_clean_baseline", "create_subscription", "read_subscription_active",
    "create_database", "read_database_active", "delete_database",
    "read_database_absent_parent_present", "delete_subscription",
    "read_subscription_absent", "complete_clean_inventory",
)
EXPECTED_EVENTS = (
    "lock", "inventory", "lock", "create subscription", "read subscription",
    "lock", "create database", "read subscription", "read database", "lock",
    "delete database", "read database", "read subscription", "lock",
    "delete subscription", "read subscription", "inventory",
)


class SimulatedPulumiAdapter:
    """A simulated scenario consumer; every result is fixture-only."""

    def execute(self, scenario):
        base = dict(provider="pulumi", scenario_id=scenario.id, mode="simulated",
                    source_revision="0" * 40, artifact_digest="", run_url="https://fixture.invalid/run",
                    evidence_url="https://fixture.invalid/log", direct_cloud_recovery=False)
        if scenario.id != "essentials-database-lifecycle":
            return Evidence(**base, steps=(), outcome="unsupported", cleanup="not_started")
        if scenario.steps != LIFECYCLE:
            return Evidence(**base, steps=(), outcome="blocked", cleanup="not_started")
        backend = FakeBackend()
        try:
            run_model(backend, "fake-account", "pulumi-proof-fixture")
        except ProofError:
            return Evidence(**base, steps=(), outcome="fail", cleanup="unknown")
        if tuple(backend.events) != EXPECTED_EVENTS:
            return Evidence(**base, steps=(), outcome="fail", cleanup="unknown")
        receipts = tuple(StepReceipt(step, "passed", f"https://fixture.invalid/steps/{step}") for step in LIFECYCLE)
        return Evidence(**base, steps=receipts, outcome="pass", cleanup="clean")
