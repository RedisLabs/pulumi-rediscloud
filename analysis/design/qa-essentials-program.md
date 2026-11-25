# Essentials QA program fixture

Date: 2026-11-25  
Status: Candidate; mocked Pulumi registration only

## TLDR

Add an opt-in Essentials program path and test its generated Pulumi SDK inputs
against an in-process mocked Pulumi engine. Do not enable live QA through this
change.

## Scope

The live suite currently exercises a Pro subscription and database. Essentials
resource registration is not covered by the suite. An explicit
`includeEssentials` configuration chooses a credit-card Essentials subscription
from the returned plan and payment method, followed by a database using the
subscription's resolved integer ID. The path exports identities and endpoint
outputs; `includeDatabase=false` registers only the subscription, matching Pro.
Invalid names, plan, payment or parent ID fail before the dependent
resource is registered. The normal Pro path remains the default.

The wrapper does not set this option, and the nightly workflow is not modified.
These tests therefore create no Cloud resources. They test the actual generated
Pulumi SDK and program registration against a fake engine, not provider HTTP
operations, update, delete, complete inventories, identity recovery, or live
Cloud state. The plan lookup remains the program's fixed GCP 1GB selection.

The companion `qa_essentials_model.py` is an executable **fake-only proof
model**, not a live driver: it has no Cloud, Pulumi CLI, shared lock or
durable journal implementation. Its tests assert authenticated exact identity
reads in order, database 404 while the subscription remains present, then
subscription 404 and a complete empty run inventory. Invalid identity,
incomplete inventory, failed authentication or lost lock stops future writes.
An abstract `assert_lock` does not itself establish fencing, does not prevent
an old writer, and leaves a check-to-write race. Missing durable ownership
and post-crash recovery also make it unsuitable for live use.

The separate pull-request-only `Shared acceptance prototype` workflow checks
out the provisional Crossplane shared contract at immutable revision
`7ab7fcbb7f70c01dbf08d9df3e40f072ec24b20e`, verifies the checkout and both
file digests, and runs a Pulumi-labeled simulated adapter using its actual
scenario definition. This adapter invokes the fake model, not Pulumi or its
SDK; it hardcodes simulated mode, yields `unsupported` for the update scenario
and blocks an incompatible lifecycle definition. Its fixture result is an
unverified simulated claim, never live coverage. The separately tested Pulumi
SDK mock program is not wired to the fake model. The pin is a temporary
unmerged proposal and is not a production contract or a reason to merge it;
neutral ownership, schema compatibility and trusted evidence remain open.

## Validation and rollout

`go test ./...` in `examples/qa` covers the two resource requests, parent ID
wiring and invalid input handling; it runs under the existing required `make
test` CI gate. A future live test must obtain an enforced shared-account lock,
prove exact resource ownership and cleanup, and verify both subscription and
database 404 responses in order. Review the preview before any manual use:
switching an existing stack from Pro to Essentials changes its desired resources
and can destroy them. No account assumptions or automatic recovery are added.

Rollback removes the optional program and fixture. No ADR is needed for a test
fixture using the existing SDK; no BDR is needed because this does not change
product or support scope.
