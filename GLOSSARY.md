# Glossary

Vocabulary for this repository. Meanings live here. The gap review is [analysis/pulumi-rediscloud-gap.md](analysis/pulumi-rediscloud-gap.md). The refresh plan is [analysis/design/pulumi-provider-refresh.md](analysis/design/pulumi-provider-refresh.md). Decisions are indexed in [analysis/adr/ADR-index.md](analysis/adr/ADR-index.md).

## Acceptance

A test that creates real Redis Cloud resources. In this repository that is the nightly QA-account create-and-delete of one ACL rule, one Pro subscription, and one database. It is not a pull-request check.

Not to be confused with the boilerplate workflow `run-acceptance-tests`, which runs on pull requests and logs in to Pulumi Cloud.

Source: [the refresh plan](analysis/design/pulumi-provider-refresh.md).

## Active-Active

A Redis Cloud subscription deployed in more than one region. Terraform and Pulumi resource names use the prefix `rediscloud_active_active_` / `ActiveActive`.

Source: `provider/resources.go`; Terraform provider resources of the same name.

## Alignment

Keeping a generated Redis Cloud provider on a named `terraform-provider-rediscloud` release. The Crossplane provider records that in `docs/terraform-alignment.md` and is aligned to v2.19.3. This Pulumi provider is still generated from v1.3.1. The refresh follows that Crossplane sequence: move the generator onto a supported release, regenerate, then track later Terraform releases with a pull request that does not merge itself.

Source: `RedisLabs/crossplane-provider-rediscloud` `docs/terraform-alignment.md`.

## Any Terraform Provider

Pulumi's zero-repository way to call a Terraform provider. A program runs `pulumi package add terraform-provider RedisLabs/rediscloud` and gets a typed SDK generated locally. The plugin is Pulumi's parameterized `terraform-provider` plugin, which is a different binary from `pulumi-resource-rediscloud`.

Source: Pulumi docs, "Any Terraform Provider", read 1 November 2026.

## Automatic token mapping

The current bridge's way of naming resources. `MustComputeTokens` turns every Terraform name into a Pulumi token without a hand-written entry. `MustApplyAutoAliases` keeps an older name working after a mapping change. This repo still lists each token in `provider/resources.go`.

Source: `pulumi/pulumi-tf-provider-boilerplate` `provider/resources.go`, read 1 November 2026.

## Cloud API

The Redis Cloud REST API. The default base URL in the bridged provider is `https://api.redislabs.com/v1`, overridable with `url` / `REDISCLOUD_URL`.

This Pulumi provider does not call the Cloud API itself. The wrapped Terraform provider calls it through `rediscloud-go-api`.

Source: Terraform provider schema for `url`; `provider/resources.go`.

## Essentials

Redis Cloud fixed and free plans. Terraform resources use the prefix `rediscloud_essentials_`. This Pulumi provider has no Essentials resources. The README's "Fixed or Free" limitation is this tier.

Source: Terraform provider changelog 1.7.0; this repo's README.

## Mux

The Terraform provider serving Plugin SDK resources and Plugin Framework resources on one gRPC server. Bridge v3.142.0 wraps that server with `MuxShimWithDisjointgPF` and `MainWithMuxer`. Bridge v3.60.1, the pin in this repository, loads a provider with `shimv2.NewProvider` and cannot serve that server.

Source: bridge guide `docs/guides/upgrade-sdk-to-mux.md` at v3.142.0; Terraform `main.go` at v2.19.3.

## Native provider

A Pulumi provider whose schema and create/read/update/delete implementations are written for Pulumi. Pulumi's publishing guide reserves this for a service with no Terraform provider, or for a Pulumi API that should differ from the Terraform one.

Source: Pulumi docs, "Write a native provider", read 1 November 2026.

## Pro

Redis Cloud flexible subscription. Terraform keeps the public names `rediscloud_subscription` and `rediscloud_subscription_database` (Pulumi: `Subscription` and `SubscriptionDatabase`). The README calls this tier Flexible. In the current Terraform provider the implementation lives under `provider/pro`.

Source: this repo's README; Terraform provider `provider/sdk_provider.go` comments at v2.19.3.

## Pulumi Terraform Bridge

Official name of the library this provider is built on. Go module `github.com/pulumi/pulumi-terraform-bridge/v3`. Repository: https://github.com/pulumi/pulumi-terraform-bridge. It embeds a Terraform provider and translates Pulumi operations into that provider's create, read, update, and delete.

Aliases: bridge, Terraform bridge, tfbridge.

Source: Pulumi publishing guide, read 1 November 2026; `provider/resources.go`.

## QA account

A non-production Redis Cloud account used by the nightly acceptance job. The job reads `REDISCLOUD_ACCESS_KEY`, `REDISCLOUD_SECRET_KEY`, and `REDISCLOUD_URL` from a GitHub Actions secret. The URL in the secret selects the account. The production host `api.redislabs.com` is refused. The account name and the URL are not written in this repository.

Source: [the refresh plan](analysis/design/pulumi-provider-refresh.md).

## rediscloud-go-api

Go client module `github.com/RedisLabs/rediscloud-go-api` for the Cloud API. The Terraform provider is the caller. This repo receives it indirectly from `terraform-provider-rediscloud` v1.3.1, which selects v0.5.3.

Source: `provider/go.mod`.

## tfgen

The program `pulumi-tfgen-rediscloud` (`provider/cmd/pulumi-tfgen-rediscloud`). At build time it reads the bridged Terraform schema and writes the language SDKs and `schema.json`. The Makefile target is `tfgen`.

Source: `Makefile`, `provider/cmd/pulumi-tfgen-rediscloud/main.go`.
