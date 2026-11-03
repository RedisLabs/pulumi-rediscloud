# Pulumi Redis Cloud: how it is built, and the gap to Terraform

Status: aligned to Terraform v2.19.3. Date: 3 November 2026. Owner: Shay Berman.

The refresh plan is [analysis/design/pulumi-provider-refresh.md](design/pulumi-provider-refresh.md). The decision is [ADR-0001](adr/ADR-0001-published-bridge-mux.md), Accepted on 1 November 2026.

This is a maintainer review of `RedisLabs/pulumi-rediscloud`. It is not a Pulumi Registry page. Sources are this repository at `main` after pull request 9 (`089bcd9`, 3 November 2026), Terraform provider tag `v2.19.3` (published 28 October 2026), and Crossplane provider `main` as of 3 November 2026.

## Verdict

This repository is a Pulumi Terraform bridge. `provider/resources.go` wraps `terraform-provider-rediscloud` v2.19.3 through bridge v3.142.0 mux entrypoints. `pulumi-tfgen` writes the schema. The checked-in SDK is Go. Node.js, Python, and .NET are produced at release time. Java is not published.

The Terraform provider is the handwritten client of the Redis Cloud API, through `rediscloud-go-api` v0.52.1. The Crossplane provider is a different generator: Upjet reads the same Terraform schema and emits Kubernetes CRDs and controllers. Crossplane and Pulumi are both pinned to Terraform v2.19.3.

Coverage on this repository: **27 of 27 resources**, **29 of 29 data sources**. The schema also exposes `pulumi:providers:rediscloud/terraformConfig`, so `schema.json` lists 30 functions. The eleven tokens published in v1.3.5 keep their names. Tokens for resources and data sources added after Terraform v1.3.1 are computed.

The newest published package remains v1.3.5 (20 December 2023). The refresh is on `main` and is not tagged. Draft release notes stay on an open pull request. Java is not published.

## The current way to build a Pulumi provider

Checked on 1 November 2026 against Pulumi's publishing guide and `pulumi/pulumi-tf-provider-boilerplate` at `master`. That template requires Go 1.26.10, `pulumi-terraform-bridge` v3.142.0, and Pulumi v3.273.0. This repository matches those pins.

Pulumi documents three packages. The one you pick depends on whether a Terraform provider already exists.

| Path | When Pulumi says to use it | What you maintain |
| --- | --- | --- |
| Any Terraform Provider | A Terraform or OpenTofu provider exists and users only need to call it from Pulumi. `pulumi package add terraform-provider RedisLabs/rediscloud` generates a typed SDK inside the consumer's project. | Nothing in this repo. The consumer pins the Terraform provider version in `Pulumi.yaml`. |
| Published bridge | You want a Registry package with your name, docs, and release cadence. Bridging is how most Registry packages are built, including AWS and Google Cloud. Start from `pulumi/pulumi-tf-provider-boilerplate`. | This repository, kept current with each Terraform release. |
| Native provider | There is no Terraform provider, or the Pulumi API should differ from the Terraform one. Azure Native and Kubernetes are native. Start from `pulumi/pulumi-provider-boilerplate` and the Go provider SDK. | A second Cloud API client, beside `terraform-provider-rediscloud`. |

For Redis Cloud the Terraform provider is already the Cloud API implementation. A native Pulumi provider would reimplement that client. The published-package method remains the bridge. ADR-0001 records that choice.

## Same refresh as the Crossplane provider

The Crossplane refresh is the pattern this repository followed. Both providers generate from `terraform-provider-rediscloud`. Crossplane generates with Upjet. This repo generates with the Pulumi Terraform Bridge. The feature target is the same pin, Terraform v2.19.3.

Crossplane open gaps that do not apply here:

- Crossplane keeps a numeric subscription id on databases and does not add a subscription reference field, because its references write strings. Pulumi passes the subscription id as a program value. Pro `SubscriptionDatabase.subscriptionId` is a string so it can take `subscription.id`. Essentials database `subscriptionId` stays an integer, matching Terraform.
- Crossplane exposes three lookups and leaves the other 26 data sources as pasted ids. The Pulumi bridge exposes all 29 data sources as functions.

## How the provider is built

```
Redis Cloud API
    └── rediscloud-go-api          (handwritten client)
            └── terraform-provider-rediscloud   (handwritten Terraform resources)
                    ├── pulumi-rediscloud       (this repo: tfbridge + tfgen)
                    └── crossplane-provider-rediscloud  (Upjet)
```

Runtime path in this repo:

1. `provider/resources.go` calls `NewSdkProvider` and `NewFrameworkProvider` from `github.com/RedisLabs/terraform-provider-rediscloud` and loads them with `MuxShimWithDisjointgPF` on bridge v3.142.0.
2. The same file keeps a hand-written map for the eleven v1.3.5 tokens, computes tokens for everything else, and applies auto aliases. Provider config maps `api_key` to `REDISCLOUD_ACCESS_KEY` then `REDISCLOUD_API_KEY`, `secret_key` to `REDISCLOUD_SECRET_KEY`, and `url` to `REDISCLOUD_URL`.
3. `provider/cmd/pulumi-tfgen-rediscloud` is the build-time generator. `make tfgen` writes `schema.json`, then `go generate` embeds it.
4. `provider/cmd/pulumi-resource-rediscloud` is the binary users install. It serves the embedded schema and forwards CRUD to the Terraform provider.
5. `make build_sdks` generates the Node.js, Python, Go, and .NET SDKs. The Go SDK is checked in under `sdk/go`. The other three are gitignored and produced at release time. `build_sdks` does not build Java, and Java is not published.

`provider/go.mod` pins:

| Module | Pin |
| --- | --- |
| `terraform-provider-rediscloud` | v2.19.3 via pseudo-version `v1.9.1-0.20261028130956-ca1e97245378` |
| `pulumi-terraform-bridge/v3` | v3.142.0 |
| `pulumi/pkg/v3` and `pulumi/sdk/v3` | v3.273.0 |
| `rediscloud-go-api` | v0.52.1, indirect |
| Go language | 1.26.10 |

Pull-request CI is `.github/workflows/ci.yml` with required check `ci-success`. Nightly QA is `.github/workflows/qa-live.yaml`. Terraform and bridge trackers open pull requests and do not merge. The release workflow runs on a tag only. No tag has been cut for this refresh.

## Feature comparison

Counts are the names registered in Terraform `provider/sdk_provider.go` and `provider/framework_provider.go` at v2.19.3, and in this repository's generated `schema.json`. Pulumi names follow the bridge (`Subscription` for `rediscloud_subscription`).

Coverage: **27 of 27 resources**, **29 of 29 data sources**.

### Resources present in both

These 11 existed in Pulumi v1.3.5 and remain under the same tokens. Top-level Terraform attributes added after v1.3.1 are now in the generated schema.

| Terraform name | Pulumi name |
| --- | --- |
| `rediscloud_subscription` | `Subscription` |
| `rediscloud_subscription_database` | `SubscriptionDatabase` |
| `rediscloud_subscription_peering` | `SubscriptionPeering` |
| `rediscloud_active_active_subscription` | `ActiveActiveSubscription` |
| `rediscloud_active_active_subscription_database` | `ActiveActiveSubscriptionDatabase` |
| `rediscloud_active_active_subscription_peering` | `ActiveActiveSubscriptionPeering` |
| `rediscloud_active_active_subscription_regions` | `ActiveActiveSubscriptionRegions` |
| `rediscloud_cloud_account` | `CloudAccount` |
| `rediscloud_acl_role` | `AclRole` |
| `rediscloud_acl_rule` | `AclRule` |
| `rediscloud_acl_user` | `AclUser` |

Attributes on `rediscloud_subscription` that v1.3.1 did not have:

`redis_version`, `maintenance_windows`, `pricing`, `customer_managed_key_enabled`, `customer_managed_key_deletion_grace_period`, `customer_managed_key`, `customer_managed_key_redis_service_account`, `customer_managed_key_aws_role_arn`, `public_endpoint_access`, `prometheus_endpoint`.

Inside existing blocks: `cloud_provider.aws_account_id`, `cloud_provider.resource_tags`, and on `creation_plan`: `dataset_size_in_gb`, `query_performance_factor`, `ram_percentage`. Terraform 2.11.0 deprecated `average_item_size_in_bytes` in favor of `ram_percentage`. Terraform 2.3.0 deprecated setting `redis_version` on the subscription and moved version selection onto the database.

Attributes on `rediscloud_subscription_database` that v1.3.1 did not have:

`dataset_size_in_gb`, `redis_version`, `redis_version_actual`, `resp_version`, `ram_percentage`, `enable_passwordless`, `client_tls_certificates`, `query_performance_factor`, `enable_default_user`, `auto_minor_version_upgrade`, `tags`.

Attributes on `rediscloud_active_active_subscription` that v1.3.1 did not have:

`aws_account_id`, `redis_version`, `maintenance_windows`, `pricing`, the same customer-managed-key set as Pro, `public_endpoint_access`, `resource_tags`.

Attributes on `rediscloud_active_active_subscription_database` that v1.3.1 did not have:

`dataset_size_in_gb`, `redis_version`, `redis_version_actual`, `client_tls_certificates`, `global_enable_passwordless`, `global_enable_default_user`, `auto_minor_version_upgrade`, `global_resp_version`, `global_modules`, `tags`. Region overrides gained `override_global_enable_passwordless` and `enable_default_user`.

### Resources added since Terraform v1.3.1

These sixteen are present in the regenerated schema.

| Area | Terraform resources | Added |
| --- | --- | --- |
| Essentials (fixed and free) | `rediscloud_essentials_subscription`, `rediscloud_essentials_database` | 1.7.0, 11 June 2024 |
| GCP Private Service Connect, Pro | `rediscloud_private_service_connect`, `rediscloud_private_service_connect_endpoint`, `rediscloud_private_service_connect_endpoint_accepter` | 2.1.0, 6 February 2025 |
| GCP Private Service Connect, Active-Active | `rediscloud_active_active_private_service_connect`, `rediscloud_active_active_private_service_connect_endpoint`, `rediscloud_active_active_private_service_connect_endpoint_accepter` | 2.1.0 |
| AWS PrivateLink, Pro | `rediscloud_private_link` | 2.4.0, 19 September 2025 |
| AWS PrivateLink, Active-Active | `rediscloud_active_active_private_link` | 2.4.1, 24 September 2025 |
| Transit Gateway, Pro | `rediscloud_transit_gateway_attachment` | 1.8.0, 12 August 2024 |
| Transit Gateway, Active-Active | `rediscloud_active_active_transit_gateway_attachment` | 1.8.0 |
| Transit Gateway routes | `rediscloud_transit_gateway_route`, `rediscloud_active_active_transit_gateway_route` | 2.10.0, 22 December 2025 |
| Transit Gateway invitation acceptors | `rediscloud_transit_gateway_invitation_acceptor`, `rediscloud_active_active_transit_gateway_invitation_acceptor` | 2.9.0, 15 December 2025 |

### Data sources

Present since v1.3.5 (11): `cloud_account`, `data_persistence`, `database`, `database_modules`, `payment_method`, `regions`, `subscription`, `subscription_peerings`, `acl_user`, `acl_role`, `acl_rule`.

Added since Terraform v1.3.1 and present now (18):

| Data source | What it reads |
| --- | --- |
| `rediscloud_essentials_plan` | Essentials plans |
| `rediscloud_essentials_subscription` | Essentials subscription |
| `rediscloud_essentials_database` | Essentials database |
| `rediscloud_active_active_subscription` | Active-Active subscription |
| `rediscloud_active_active_subscription_database` | Active-Active database |
| `rediscloud_active_active_subscription_regions` | Active-Active regions |
| `rediscloud_private_service_connect` | Pro PSC service |
| `rediscloud_private_service_connect_endpoints` | Pro PSC endpoints |
| `rediscloud_active_active_private_service_connect` | Active-Active PSC service |
| `rediscloud_active_active_private_service_connect_endpoints` | Active-Active PSC endpoints |
| `rediscloud_private_link` | Pro PrivateLink |
| `rediscloud_private_link_endpoint_script` | Pro PrivateLink endpoint script |
| `rediscloud_active_active_private_link` | Active-Active PrivateLink |
| `rediscloud_active_active_private_link_endpoint_script` | Active-Active PrivateLink endpoint script |
| `rediscloud_transit_gateway` | Pro transit gateway |
| `rediscloud_active_active_transit_gateway` | Active-Active transit gateway |
| `rediscloud_transit_gateway_invitations` | Pro pending invitations |
| `rediscloud_active_active_transit_gateway_invitations` | Active-Active pending invitations |

### Provider configuration

Terraform accepts `api_key`, `secret_key`, and `url`. Pulumi exposes the same three, as `apiKey`, `secretKey`, and `url`.

`api_key` reads `REDISCLOUD_ACCESS_KEY` first, then `REDISCLOUD_API_KEY`. `REDISCLOUD_ACCESS_KEY` wins when both are set. `REDISCLOUD_API_KEY` remains so a v1.3.5 setup that only sets that name keeps working. `secret_key` stays `REDISCLOUD_SECRET_KEY`. `url` reads `REDISCLOUD_URL`.

## Version alignment

| Component | Pinned in this repo | Notes |
| --- | --- | --- |
| Go in `provider/go.mod` and `sdk/go.mod` | 1.26.10 | Same toolchain as Terraform v2.19.3 |
| Node.js in the SDK job | 24.x | Release workflow |
| Python in the SDK job | 3.13 | Release workflow |
| .NET SDK in the SDK job | .NET 10 when the package is built | `NUGET_PUBLISH` stays false |
| Java publish | off | `JAVA_PUBLISH` false; out of the publish matrix |
| GoReleaser | v2 `--clean` | Tag-only `release.yaml` |
| Pulumi SDK | v3.273.0 | |
| `pulumi-terraform-bridge` | v3.142.0 | Mux entrypoints |
| `terraform-provider-rediscloud` | v2.19.3 | Pseudo-version in `provider/go.mod` |
| `rediscloud-go-api` | v0.52.1 | Transitive |

## What remains open

1. Draft release notes stay open. Do not tag. Newest published release stays v1.3.5.
2. Java publication waits on a later decision (T11).
3. NuGet stays unpublished.
4. A newer Terraform release opens a pull request through the tracker. That pull request does not merge itself. Do not regenerate for a tag that does not exist.

## What this review did not do

This update records the post-refresh state on `main`. It does not publish a package and does not call the Cloud API. Nested schema diffs for peering, ACL, and cloud account stop at the top-level keys plus the Terraform changelog. The attribute lists for subscription and database remain the v1.3.1 to v2.19.3 delta used when planning the major.
