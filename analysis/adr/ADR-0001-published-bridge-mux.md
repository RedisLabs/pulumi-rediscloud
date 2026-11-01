# ADR-0001: Stay on the published bridge and move to the mux entrypoints

Status: Proposed.
Date: 1 November 2026.
Decision owner: Shay Berman.
Index: [ADR-index.md](ADR-index.md).
Design: [pulumi-provider-refresh.md](../design/pulumi-provider-refresh.md).
Ticket: none.
BDR: none.

## Context

`pulumi-rediscloud` v1.3.5 is a published Pulumi package. Stacks install the plugin `pulumi-resource-rediscloud`. The module pins Pulumi Terraform Bridge v3.60.1 and Terraform provider v1.3.1, and it loads that provider with `shimv2.NewProvider`.

Terraform v2.19.3 serves Plugin SDK resources and Plugin Framework resources through one muxed server. Bridge v3.142.0, released 27 October 2026, is the current boilerplate pin and is the latest bridge release as of 1 November 2026. Its mux guide wraps that server with `MuxShimWithDisjointgPF` and the `MainWithMuxer` entrypoints. Those entrypoints are marked experimental. Pulumi's guide says production providers use them.

The Terraform provider remains the Cloud API client. The Crossplane provider generates from the same Terraform module with a different tool.

## Alternatives

| Alternative | Why it is not the decision |
| --- | --- |
| Any Terraform Provider, and no further releases of this repo | Fits a new program. An existing stack is bound to `pulumi-resource-rediscloud`. Changing an import does not move it. |
| A native provider written against the Cloud API | A second client beside `terraform-provider-rediscloud`. The feature gap is the Terraform gap, which regeneration closes. |
| Bump bridge v3.60.1 in `go.mod` and keep `shimv2.NewProvider` | That entrypoint does not load the muxed Terraform server. The module would not build. |
| Run `ci-mgmt` acceptance tests on every pull request | That workflow calls Pulumi Cloud and runs on pull requests. The Redis Cloud live suite stays off pull requests, matching the Crossplane nightly. |
| Mint a throwaway Cloud account per run, as the Terraform provider does | That flow is separate from this repository. This plan uses one QA account credential. |

## Decision

Stay a published bridge. In one change, move to bridge v3.142.0, Pulumi v3.273.0, Go 1.26.10, and Terraform v2.19.3, and load the provider through the mux entrypoints. Keep the Pulumi tokens v1.3.5 already published. Do not tag a release as part of accepting this record.

Later bridge releases are their own pull request. They do not move the Terraform pin. The first jump is done by hand because the entrypoint has to change. A workflow cannot carry v3.60.1 onto the mux entrypoints.

## Consequences

- T1 in the design is one pull request. Splitting the bridge bump from the Terraform bump does not compile.
- Existing token names stay. Behavior changes from Terraform v1.3.1 to v2.19.3 still make the unpublished release a new major.
- `MainWithMuxer` is the supported production path Pulumi documents, and it is still marked experimental upstream. A removal upstream is the revisit condition.
- Java publication is out of this decision. The design defers it.

## Revisit

Revisit when Pulumi removes or replaces `MainWithMuxer`, or when a Redis Cloud change needs a Pulumi API that the Terraform schema cannot express. Either event reopens the native-provider alternative. It does not by itself mean this package should stop publishing.
