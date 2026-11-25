# QA writer serialization and safe recovery

Date: 2026-11-25  
Status: Candidate; credential-free validation only

## TLDR

Defer the scheduled and manual QA writer until a shared account lock and safe
recovery are available. Refuse prefix-based and name-only direct API cleanup.
After a failed operation, do not automatically retry destroy: a child create or
destroy may already have been accepted even though the response was lost.

## Problem and behavior

GitHub Actions concurrency only serializes runs in this repository. Other
connectors may use the same Redis Cloud account, so the same group name does
not prevent overlapping Cloud mutations. The account equivalence has not been
verified. The previous preflight deleted every subscription with a shared test
prefix; a prefix, or a run-derived name alone, is not proof of ownership.
The old direct cleanup enumerated only one page of children and could delete
unrelated databases. These are unsafe assumptions even in a QA account.

The new job gate fails before checkout, credentials, or Cloud calls for both
schedule and dispatch. A workflow already running continues on its original
revision; its existing cleanup is not cancelled. The wrapper refuses any
prefixed leftover, rejects malformed and explicitly incomplete inventories,
and holds direct recovery rather than sending DELETE. An accepted Pulumi
destroy within the existing runner uses that runner's Pulumi state; it does not
make cross-repository concurrency safe. No workflow bypass is provided.

## Validation and limitations

Credential-free tests exercise a lost response after a fake child create and
after a fake destroy (no parent cleanup or destroy replay), failure before
creation, preservation of a different run's subscription, refusal of same-name
recovery, malformed/partial inventories, and the failing gate dependency. Required
CI runs this suite. The success-path fixture is a fake HTTP server and does not
establish live Cloud behavior. Missing
pagination metadata and silent truncation cannot be disproved by these tests.
Any nonempty `links` or `_links` also causes a hold, including a self link;
the live response contract needs verification before relaxing this guard.
Existing workflow runs and reruns of older commits use their original files and
can bypass the new gate; other repositories and local tools are also outside
this gate. It is a mitigation, not a shared lock. A failed run can leave resources
behind and requires recovery from independently established ownership and state;
the ephemeral runner's Pulumi state and a post-job artifact are not a durable
journal. An intent record by itself cannot resolve a create with unknown outcome.
A future design needs durable state and journal writes before each mutation, an
authoritative fencing boundary, and a reviewed process for ambiguous outcomes.

## Rollout, recovery, and next steps

On merge, new scheduled and manually dispatched acceptance runs will fail with
an explicit DEFER, so the dashboard must not call them passing. Preserve existing
in-flight jobs and cleanup. Do not recover an unknown resource from a name alone;
establish account identity, exact resource ownership, complete inventories and
an authoritative exclusion protocol first. Restore live testing only after all
writers participate in a durable lock and controlled crash/cleanup rehearsal.
Rollback re-enables unsafe execution and therefore requires equivalent external
serialization and reviewed cleanup controls first.

The design updates the existing QA workflow, not an external API. No new ADR or
BDR is required: it defers an unsafe path while the lock contract is unresolved.
