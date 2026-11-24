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
