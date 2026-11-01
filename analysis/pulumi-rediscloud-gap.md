# Pulumi Redis Cloud: how it is built, and the gap to Terraform

Status: review. Date: 1 November 2026. Owner: Shay Berman.

The refresh plan, with the task graph, is [analysis/design/pulumi-provider-refresh.md](design/pulumi-provider-refresh.md). The decision is [ADR-0001](adr/ADR-0001-published-bridge-mux.md), still Proposed.

This is a maintainer review of `RedisLabs/pulumi-rediscloud`. It is not a Pulumi Registry page. Sources are this repository at `main` (`6a6fa7d`, 22 January 2024), Terraform provider tag `v2.19.3` (published 28 October 2026; `main` is the same commit), and Crossplane provider `main` as of 31 October 2026.

## Verdict

This repository is a Pulumi Terraform bridge. A small hand-written file wraps `terraform-provider-rediscloud` v1.3.1. `pulumi-tfgen` then generates the Go, Node.js, Python, .NET, and Java SDKs from that Terraform schema.

The Terraform provider is the handwritten client of the Redis Cloud API, through `rediscloud-go-api`. The Crossplane provider is a different generator: Upjet reads the Terraform schema and emits Kubernetes CRDs and controllers. Crossplane is pinned to Terraform v2.19.3. Pulumi is pinned to Terraform v1.3.1.

The last commit on this repository is 22 January 2024. That is 1,014 days before 1 November 2026. The last GitHub release is v1.3.5, published 20 December 2023 (1,047 days). The Terraform provider has published through v2.19.3 in that interval, including the v2.0.0 break on 5 December 2024.

## The current way to build a Pulumi provider

Checked on 1 November 2026 against Pulumi's publishing guide and `pulumi/pulumi-tf-provider-boilerplate` at `master` (template workflows updated 31 October 2026). That template requires Go 1.26.10, `pulumi-terraform-bridge` v3.142.0, and Pulumi v3.273.0.

Pulumi documents three packages. The one you pick depends on whether a Terraform provider already exists.

| Path | When Pulumi says to use it | What you maintain |
| --- | --- | --- |
| Any Terraform Provider | A Terraform or OpenTofu provider exists and users only need to call it from Pulumi. `pulumi package add terraform-provider RedisLabs/rediscloud` generates a typed SDK inside the consumer's project. | Nothing in this repo. The consumer pins the Terraform provider version in `Pulumi.yaml`. |
| Published bridge | You want a Registry package with your name, docs, and release cadence. Bridging is how most Registry packages are built, including AWS and Google Cloud. Start from `pulumi/pulumi-tf-provider-boilerplate`. | This repository, kept current with each Terraform release. |
| Native provider | There is no Terraform provider, or the Pulumi API should differ from the Terraform one. Azure Native and Kubernetes are native. Start from `pulumi/pulumi-provider-boilerplate` and the Go provider SDK. | A second Cloud API client, beside `terraform-provider-rediscloud`. |

For Redis Cloud the Terraform provider is already the Cloud API implementation. A native Pulumi provider would reimplement that client. The current published-package method is still the bridge.

The current bridge template differs from this repo in four places:

1. Tokens are computed, not listed by hand. `MustComputeTokens(tokens.SingleModule(...))` maps every Terraform resource and data source. `MustApplyAutoAliases` keeps an old Pulumi name working when the mapping changes. This repo lists all 11 resources and 11 data sources in `provider/resources.go`. New Terraform resources stay invisible until someone adds a line.
2. `bridge-metadata.json` is embedded and records the dispatch table. This repo has no such file.
3. CI comes from `pulumi/ci-mgmt` (`make ci-mgmt`, config in `.ci-mgmt.yaml`). The generated workflows include `upgrade-bridge.yml` and `upgrade-provider.yml`. Publishing SDKs goes through `pulumi/pulumi-package-publisher`. The external template publishes Node.js, Python, .NET, and Go, and leaves Java off. This repo has one hand-written GoReleaser workflow.
4. A provider that mixes Plugin SDK v2 and Plugin Framework uses the mux entrypoints in bridge v3.142.0, documented in `docs/guides/upgrade-sdk-to-mux.md`. Terraform Redis Cloud v2.19.3 is that shape: `main.go` serves `MuxProviderServerCreator` with `NewSdkProvider` and `NewFrameworkProvider`. The bridge call is `pftfbridge.MuxShimWithDisjointgPF` when each token has one owner, then `pf/tfgen.MainWithMuxer` and `pf/tfbridge.MainWithMuxer`. Pulumi marks those two `MainWithMuxer` functions experimental and says production providers use them. This repo calls `shimv2.NewProvider`, which only accepts the Plugin SDK.

`provider/go.mod` cannot take Terraform v2.19.3 on the code that is here. The refresh is a move onto the current template, with the existing Pulumi names (`Subscription`, `SubscriptionDatabase`, and the rest) kept as manual overrides so stacks created with v1.3.5 keep their tokens.

Any Terraform Provider is the path with no repository. It runs inside Pulumi's parameterized `terraform-provider` plugin. Programs that already use `pulumi-resource-rediscloud` from GitHub Releases are bound to this repo's plugin, so changing an import does not move an existing stack.

## Same refresh as the Crossplane provider

The Crossplane refresh is the pattern to follow. Both providers generate from `terraform-provider-rediscloud`. Crossplane generates with Upjet. This repo generates with the Pulumi Terraform Bridge. The feature target is the same pin, Terraform v2.19.3.

Sources, read 1 November 2026:

- Gap tracker: [`docs/terraform-alignment.md`](https://github.com/RedisLabs/crossplane-provider-rediscloud/blob/main/docs/terraform-alignment.md) on Crossplane `main` (`a2b716c`). Nine numbered gaps. Managed resources are 27 of 27. Three lookups exist. The other 26 data sources stay pasted IDs.
- Release notes, still unpublished: [pull request 20](https://github.com/RedisLabs/crossplane-provider-rediscloud/pull/20), file `docs/release-notes/unreleased.md`. The pull request says not to merge it. No git tag and no package have been published.

What that refresh actually did, in merge order:

| Crossplane pull request | What it changed | Pulumi equivalent |
| --- | --- | --- |
| 2 | Regenerated every managed resource from Terraform v2.19.2. Coverage went from 21 resources on v2.1.5 to 27. | Regenerate from v2.19.3. Coverage here is 11 resources and 11 data sources, on Terraform v1.3.1. |
| 12 | Moved the generator off end-of-life versions: Upjet v1.4.1 and Crossplane 1.16 to Upjet v2.5.1, Crossplane 2.4.3, Go 1.26.8. | Move off bridge v3.60.1, Go 1.18, and the Plugin SDK fork. Land on bridge v3.142.0, Go 1.26.10, and the mux entrypoints. The old bridge cannot load Terraform v2.19.3. |
| 3 | Added the three lookups an install cannot proceed without: payment method, Essentials plan, region. | The Pulumi bridge already turns Terraform data sources into functions. Regenerating emits all 29, including those three. No separate lookup CRDs. |
| 5, then 18 | A workflow opens a pull request when Terraform publishes a release. v2.19.3 arrived that way. The workflow does not merge, and it does not bump the generator. | After the first regenerate, the same kind of workflow. The current boilerplate also has `upgrade-provider.yml` from `ci-mgmt`. |
| 7–11, 14 | Required CI check, alignment guards, nightly create-and-delete on the QA Redis Cloud account, `govulncheck`. | This repo has no pull-request CI. The release workflow is the only workflow, and its actions are past the GitHub Actions runtime. |
| 13 | Stored API moved from `v1alpha1` to `v1beta1`, and `v1alpha1` stayed served. | Existing stacks already use Pulumi tokens such as `Subscription`. Keep those names with manual overrides and `MustApplyAutoAliases`. This package is already published as v1.3.5, so the refresh is a new major. Crossplane had never published a package. |
| 15–17 | Locked passwordless omission, kept served API files during generate, ignored the release bundle. | Schema behavior comes from Terraform once the bridge is current. The publish path still has to be replaced: Node 24 actions, GoReleaser v2, Maven Central Portal. |
| 19 | Recorded v2.19.3 in the alignment doc. | Update this file's pin when the regenerate lands. |
| [20](https://github.com/RedisLabs/crossplane-provider-rediscloud/pull/20), open | Draft release notes for review. Do not merge. Do not tag. | Write the Pulumi notes the same way, and do not tag until they are accepted. |

The release notes state the motivation in one place: the provider had been sitting on versions that left support, and the update moves each one onto a current release and closes the feature gap with Terraform. That sentence fits this repo. The versions named there are Upjet, Crossplane, Go, and the Kubernetes clients. The versions to name here are the Pulumi Terraform Bridge, Go, the language runtimes in the release job, and Terraform v1.3.1 to v2.19.3.

Two Crossplane decisions do not copy across. Databases keep a numeric subscription id with no `subscriptionIdRef`, because Crossplane references write strings. Pulumi passes the subscription id as a program value, which is the Terraform interpolation. And Crossplane left 26 data sources as pasted IDs. A regenerated Pulumi SDK exposes those data sources as functions.

## How the provider is built

```
Redis Cloud API
    └── rediscloud-go-api          (handwritten client)
            └── terraform-provider-rediscloud   (handwritten Terraform resources)
                    ├── pulumi-rediscloud       (this repo: tfbridge + tfgen)
                    └── crossplane-provider-rediscloud  (Upjet)
```

Runtime path in this repo:

1. `provider/resources.go` calls `rediscloud.New("pulumi")()` from `github.com/RedisLabs/terraform-provider-rediscloud` and passes the provider to `pulumi-terraform-bridge` v3.60.1.
2. The same file maps each Terraform name to a Pulumi token (`rediscloud_subscription` becomes `Subscription`) and overrides a few schema details, including the API-key environment variable.
3. `provider/cmd/pulumi-tfgen-rediscloud` is the build-time generator. `make tfgen` writes `schema.json`, then `go generate` embeds it.
4. `provider/cmd/pulumi-resource-rediscloud` is the binary users install. It serves the embedded schema and forwards CRUD to the Terraform provider.
5. `make build_sdks` generates the language SDKs. The Go SDK is checked in under `sdk/go`. Node.js, Python, .NET, and Java are gitignored and produced at release time.

The only product code that is original to this repo is the bridge metadata in `resources.go`, the release wiring, examples, and docs. Resource behavior lives in the Terraform provider, which calls `rediscloud-go-api`.

`provider/go.mod` pins:

| Module | Pin |
| --- | --- |
| `terraform-provider-rediscloud` | v1.3.1 |
| `pulumi-terraform-bridge/v3` | v3.60.1 |
| `pulumi/sdk/v3` | v3.81.0 |
| `terraform-plugin-sdk/v2` | replaced with the Pulumi fork `v2.0.0-20230912190043-e6d96b3b8f7e` |
| `rediscloud-go-api` | v0.5.3, indirect |
| Go language | 1.18 in `provider/go.mod`, 1.17 in `sdk/go.mod` |

There is no pull-request CI workflow. `.github/workflows/release.yaml` is the only workflow. `make test` runs the examples, and those examples create real Redis Cloud resources.

## How it is published

A tag matching `v*.*.*` starts `.github/workflows/release.yaml`.

1. **Provider binary.** GoReleaser builds `pulumi-resource-rediscloud` for linux, darwin, and windows, on amd64 and arm64, with `CGO_ENABLED=0`. The GitHub release is the plugin source. Install with `pulumi plugin install resource rediscloud <version> --server github://api.github.com/RedisLabs`.
2. **SDK tag.** The workflow creates `sdk/<tag>` on the same commit.
3. **Language packages**, after the provider job:
   - npm: `@rediscloud/pulumi-rediscloud` (`NPM_PUBLISH: true`)
   - PyPI: `pulumi_rediscloud` (`PYPI_PUBLISH: true`)
   - NuGet: built, and `NUGET_PUBLISH` is false
   - Java: Gradle `publishToSonatype closeAndReleaseSonatypeStagingRepository`
   - Go: the module `github.com/RedisLabs/pulumi-rediscloud/sdk`

Published release line: v1.1.1 through v1.3.5, all in May–December 2023. v1.3.2 through v1.3.5 are packaging and Java-publish fixes. They did not move the Terraform dependency past v1.3.1. That dependency was set on 28 September 2023 (`feat: update to latest provider`), when v1.3.1 was current. Terraform v1.3.2 came out on 9 October 2023.

The release workflow itself is past the runtimes it needs. See the version table below. A tag push on 1 November 2026 would fail before it compiled the provider.

## How long it has been untouched

| Event | Date | Age on 1 November 2026 |
| --- | --- | --- |
| First commit, `feat: initial provider with Go SDK` | 9 May 2023 | |
| Terraform dependency set to v1.3.1 | 28 September 2023 | |
| Last GitHub release, v1.3.5 | 20 December 2023 | 1,047 days |
| Last commit, docs only (`6a6fa7d`, Ringo De Smet) | 22 January 2024 | 1,014 days |
| Terraform v2.0.0 | 5 December 2024 | after the last Pulumi commit |
| Terraform v2.19.3, current `main` | 28 October 2026 | 1,175 days after Terraform v1.3.1 (10 August 2023) |
| Crossplane provider last commit on `main` | 31 October 2026 | draft release v0.1.0 the same day; package not published |

60 commits total, all on `main`, which matches `origin/main`.

## Three generators, one API

| | Terraform provider | This Pulumi provider | Crossplane provider |
| --- | --- | --- | --- |
| Repository | `RedisLabs/terraform-provider-rediscloud` | `RedisLabs/pulumi-rediscloud` | `RedisLabs/crossplane-provider-rediscloud` |
| How the resources are produced | Handwritten against `rediscloud-go-api` | Bridge metadata plus `tfgen` over the Terraform schema | Upjet over the Terraform schema |
| Terraform pin | the provider itself, v2.19.3 | v1.3.1 | v2.19.3 |
| Cloud API client | `rediscloud-go-api` v0.52.1 | v0.5.3 | v0.52.1 |
| Go | 1.26.0, toolchain 1.26.10 | 1.18 declared; CI uses 1.19 and 1.20 | 1.26.8, toolchain 1.26.10 |
| Terraform implementation | Plugin SDK v2.40.1 muxed with Plugin Framework v1.19.0 | Plugin SDK v2.26.1 through the 2023 Pulumi fork | Upjet v2.5.1 reading the Terraform schema |
| Managed resources | 27 | 11 | 27, the same Terraform resources, as `v1beta1` CRDs |
| Data sources / lookups | 29 | 11 | lookups stay `v1alpha1`; managed resources are the 27 |
| Latest published artifact | v2.19.3 on 28 October 2026 | v1.3.5 on 20 December 2023 | draft v0.1.0 on 31 October 2026; the README says the image is not in the Crossplane registry |

Crossplane is the generated sibling, and it is already on the current Terraform provider. Pulumi is the same idea (generate from the Terraform schema) with an older generator and a 2023 snapshot of that schema. Refreshing Pulumi means moving the bridge onto Terraform v2.19.3. It does not mean reimplementing the Cloud API the way the Terraform provider does.

A version bump of `terraform-provider-rediscloud` in `provider/go.mod` is not enough:

- Several current resources and data sources are Terraform Plugin Framework types, muxed with the SDK provider. Bridge v3.60.1 predates that. Current bridge v3.142.0 (27 October 2026) targets upstream Plugin SDK and runs on Go 1.26.10.
- `resources.go` lists every token by hand. New Terraform resources stay invisible until they are added there and the SDKs are regenerated.
- Terraform v2.0.0 removed `latest_backup_status` and `latest_import_status`. Those fields arrived in Terraform 1.7.0, so this Pulumi package never had them. Later Terraform releases still change defaults on resources this package does have (`payment_method` ignored after create, `auto_minor_version_upgrade` defaulting to true, `redis_version` moving from the subscription onto the database). A bridge refresh is a new major for anyone with an existing stack.

## Feature comparison

Counts are the names registered in Terraform `provider/sdk_provider.go` and `provider/framework_provider.go` at v2.19.3, and in `provider/resources.go` here. Pulumi names follow the bridge (`Subscription` for `rediscloud_subscription`).

Coverage: **11 of 27 resources**, **11 of 29 data sources**.

### Resources present in both

These 11 exist in Pulumi v1.3.5 and Terraform v2.19.3. "Same top-level keys" means the Terraform schema's top-level attribute set matches v1.3.1. Nested fields can still differ; those are called out where the v2.19.3 schema or changelog names them.

| Terraform name | Pulumi name | Top-level schema since v1.3.1 |
| --- | --- | --- |
| `rediscloud_subscription` | `Subscription` | 10 attributes added. See below. |
| `rediscloud_subscription_database` | `SubscriptionDatabase` | 11 attributes added. See below. |
| `rediscloud_subscription_peering` | `SubscriptionPeering` | Same 14 top-level keys. |
| `rediscloud_active_active_subscription` | `ActiveActiveSubscription` | 11 attributes added. See below. |
| `rediscloud_active_active_subscription_database` | `ActiveActiveSubscriptionDatabase` | Moved to Plugin Framework. Attributes added below. |
| `rediscloud_active_active_subscription_peering` | `ActiveActiveSubscriptionPeering` | Same 15 top-level keys. |
| `rediscloud_active_active_subscription_regions` | `ActiveActiveSubscriptionRegions` | Same 3 top-level keys. `region_id` was added on region objects and on the regions data source (Terraform 2.4.1 and 2.8.0). |
| `rediscloud_cloud_account` | `CloudAccount` | Moved to Plugin Framework in Terraform 2.19.0. User-facing fields match; the framework schema also exposes `id`. |
| `rediscloud_acl_role` | `AclRole` | Same top-level keys. |
| `rediscloud_acl_rule` | `AclRule` | Same top-level keys. |
| `rediscloud_acl_user` | `AclUser` | Same top-level keys. |

Attributes on `rediscloud_subscription` that v1.3.1 does not have:

`redis_version`, `maintenance_windows`, `pricing`, `customer_managed_key_enabled`, `customer_managed_key_deletion_grace_period`, `customer_managed_key`, `customer_managed_key_redis_service_account`, `customer_managed_key_aws_role_arn`, `public_endpoint_access`, `prometheus_endpoint`.

Inside existing blocks: `cloud_provider.aws_account_id`, `cloud_provider.resource_tags`, and on `creation_plan`: `dataset_size_in_gb`, `query_performance_factor`, `ram_percentage`. Terraform 2.11.0 deprecated `average_item_size_in_bytes` in favor of `ram_percentage`. Terraform 2.3.0 deprecated setting `redis_version` on the subscription and moved version selection onto the database.

Attributes on `rediscloud_subscription_database` that v1.3.1 does not have:

`dataset_size_in_gb`, `redis_version`, `redis_version_actual`, `resp_version`, `ram_percentage`, `enable_passwordless`, `client_tls_certificates`, `query_performance_factor`, `enable_default_user`, `auto_minor_version_upgrade`, `tags`.

Attributes on `rediscloud_active_active_subscription` that v1.3.1 does not have:

`aws_account_id`, `redis_version`, `maintenance_windows`, `pricing`, the same customer-managed-key set as Pro, `public_endpoint_access`, `resource_tags`.

Attributes on `rediscloud_active_active_subscription_database` that v1.3.1 does not have:

`dataset_size_in_gb`, `redis_version`, `redis_version_actual`, `client_tls_certificates`, `global_enable_passwordless`, `global_enable_default_user`, `auto_minor_version_upgrade`, `global_resp_version`, `global_modules`, `tags`. Region overrides gained `override_global_enable_passwordless` and `enable_default_user`.

Peering, ACL, and cloud account were not re-diffed field by field below the top level. The changelog from 1.4.0 through 2.19.3 does not add a new resource in those four areas; it does fix ACL rule updates and cloud-account wait behavior.

### Resources only in Terraform v2.19.3

Pulumi has none of these. Crossplane generates all of them.

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

The README in this repo still says the provider is for Flexible or Annual subscriptions and is not supported for Fixed or Free. That matches the pinned Terraform provider. Terraform has covered Essentials since 1.7.0. Current Terraform also covers Redis 8 and 8.2, customer-managed keys (GCP, then AWS), passwordless databases when the public endpoint is off, query performance factor, Prometheus endpoint, and subscription `resource_tags`.

### Data sources

Present in both (11): `cloud_account`, `data_persistence`, `database`, `database_modules`, `payment_method`, `regions`, `subscription`, `subscription_peerings`, `acl_user`, `acl_role`, `acl_rule`.

The Pro subscription and database data sources grew the same customer-managed-key, pricing, tags, Redis version, and passwordless fields as the resources. `rediscloud_regions` gained `region_id`. Several of these data sources were rewritten on the Plugin Framework during 2026 with the changelog claiming no schema change, then 2.19.2 and 2.19.3 fixed plan-time unknown values for `pricing`, `maintenance_windows`, and `cloud_provider`.

Only in Terraform v2.19.3 (18):

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

The bridged schema's description says the API key can come from `REDISCLOUD_ACCESS_KEY`, which is what `rediscloud-go-api` reads (`AccessKeyEnvVar` in v0.52.1) and what this repo's README documents. The bridge overlay in `resources.go` sets the Pulumi default to `REDISCLOUD_API_KEY` instead. The secret default is `REDISCLOUD_SECRET_KEY` on both sides. `url` documents `REDISCLOUD_URL` and the Terraform schema has `DefaultFunc` for it; the Pulumi schema does not add its own environment default for `url`.

## Version alignment

"EOF" means the vendor's stated end of support was already past on 1 November 2026. Dates are from Go's release history, [nodejs/Release](https://github.com/nodejs/release), [Python devguide](https://devguide.python.org/versions/), Microsoft's .NET lifecycle, [Adoptium Temurin support](https://adoptium.net/support), the [GitHub changelog of 23 September 2026](https://github.blog/changelog/2026-09-23-node-20-is-no-longer-available-in-github-actions/) (Node 20 removed from Actions runners), and [Sonatype's OSSRH sunset](https://central.sonatype.org/pages/ossrh-eol/) (30 June 2025).

The alignment target follows the Redis Cloud generators that are already current: Terraform and Crossplane on Go 1.26.10, Terraform provider v2.19.3, and Pulumi bridge v3.142.0. Go 1.27.3 is also supported. Pinning 1.26.10 keeps Pulumi on the same toolchain as the provider it would wrap. Node 22 is still in maintenance through 30 April 2027; Node 24 through 30 April 2028; Node 26 is the Active LTS. Python 3.10 also ended on 1 October 2026, so the next Python pin should be 3.12 or newer. .NET 8 and .NET 9 both end support on 10 November 2026. .NET 10 is the LTS through 14 November 2028. Java 11 is still an Adoptium LTS "at least through October 2027", so it is not EOF. Java 21 runs at least through December 2029.

| Component | Pinned in this repo | Status on 1 November 2026 | Align to |
| --- | --- | --- | --- |
| Go in `provider/go.mod` | 1.18 | EOF since 1 February 2023 | 1.26.10 |
| Go in the provider release job | 1.19.x | EOF since 6 September 2023 | 1.26.10 |
| Go in the SDK release job | 1.20.x | EOF since 6 February 2024 | 1.26.10 |
| Go in `sdk/go.mod` | 1.17 | EOF since 2 August 2022 | regenerated SDK on 1.26.10 |
| Node.js in the SDK job | 16.x | EOF since 11 September 2023 | 24.x, or 22.x through April 2027 |
| Python in the SDK job | 3.9 | EOF since 31 October 2025 | 3.13 (security fixes through October 2029) |
| .NET SDK in the SDK job | 3.1.301 | EOF since 13 December 2022. NuGet publish is already off | .NET 10 if NuGet publishing is turned on |
| Java in the SDK job | 11 | Still available from Temurin at least through October 2027 | 21 |
| Gradle | 7.6 to set up, 7.4.1 to publish | Old. The publish task is the broken part | the Gradle emitted by current `pulumi-java` |
| Maven Central publish | OSSRH `closeAndReleaseSonatypeStagingRepository` with `OSSRH_USERNAME` / `OSSRH_PASSWORD` | OSSRH shut down 30 June 2025 | Central Portal token, `pulumi-java` v1.38.0 (28 October 2026) |
| `pulumi-java` / `pulumi-language-java` | CI downloads v0.9.4; Makefile says v0.9.8 | 0.9.x emits the OSSRH Gradle files | v1.38.0 |
| GitHub Actions JavaScript runtime | checkout v3.5.2, setup-go v4, setup-node v3, setup-python v4, setup-dotnet v2, setup-java v3, github-script v6, gradle-build-action v2, goreleaser-action v4 | Node 20 was removed from GitHub-hosted runners on 23 September 2026. These pins target Node 16 or Node 20 | current Node 24 majors (`actions/checkout` v5 and the matching setup actions) |
| GoReleaser | action `version: latest`, args include `--rm-dist` | Latest stable is v2.19.0 (22 October 2026). v2 replaced `--rm-dist` with `--clean` | GoReleaser v2 config and `--clean` |
| `pulumictl` | v0.0.43 | Latest is v0.0.50 (31 July 2025). The 0.0.x line is still the current line | v0.0.50 |
| Pulumi SDK | provider v3.81.0; checked-in Go SDK requires v3.38.0 | 3.x is still the supported line. Current CLI and SDK are v3.273.0 (28 October 2026) | v3.273.0 |
| `pulumi-terraform-bridge` | v3.60.1 | Current is v3.142.0 (27 October 2026), Go 1.26.10. v3.141 moved off the Pulumi Plugin SDK fork onto upstream | v3.142.0 |
| `terraform-plugin-sdk/v2` | v2.26.1 via the Pulumi fork commit of 12 September 2023 | Upstream in Terraform v2.19.3 is v2.40.1 | drop the `replace`; take the version the bridge selects |
| Terraform Plugin Framework | not a dependency | Terraform v2.19.3 requires v1.19.0 and serves cloud account, Active-Active database, and many data sources through it | arrive via the bridged provider, not as a direct Pulumi dependency |
| `terraform-provider-rediscloud` | v1.3.1 (10 August 2023) | Current release v2.19.3 (28 October 2026) | v2.19.3 |
| `rediscloud-go-api` | v0.5.3 | Current v0.52.1, same pin as Terraform v2.19.3 and Crossplane | v0.52.1, transitively |

Plugin pins that exist only so example programs install are also old: the release job installs Pulumi AWS 5.40.0 and GCP 6.55.1, and the Makefile installs `random` 4.3.1. Those are not Redis Cloud features. They do not need to move until the examples are regenerated.

## What a refresh has to change

1. Replace bridge v3.60.1 and Pulumi SDK v3.81.0 with v3.142.0 and v3.273.0, on Go 1.26.10, and delete the Plugin SDK `replace`.
2. Point `terraform-provider-rediscloud` at v2.19.3.
3. Register the 16 missing resources and 18 missing data sources in `resources.go`, then regenerate every SDK.
4. Decide the Pulumi major version. Terraform 2.x changes defaults and deprecations on `Subscription` and `SubscriptionDatabase`, which existing Pulumi stacks already use.
5. Replace the release workflow: Node 24 actions, Go 1.26.10, Node 24, Python 3.13, Java 21, `pulumi-java` 1.38.0, Central Portal publishing, GoReleaser v2.
6. Point the API-key default at `REDISCLOUD_ACCESS_KEY` so the overlay matches the Cloud API client and the README.

## What this review did not do

The provider was not compiled, and the release workflow was not re-run. The GitHub Actions and OSSRH conclusions come from the pinned files plus the vendor end-of-support notices above. Nested schema diffs for peering, ACL, and cloud account stop at the top-level keys plus the Terraform changelog. The attribute lists for subscription and database were taken from the v1.3.1 and v2.19.3 schema maps.
