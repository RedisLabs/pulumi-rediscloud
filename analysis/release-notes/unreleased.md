# Unreleased

Do not tag this refresh. v1.3.5 remains the latest installable release until a later decision tags v2.0.0.

## Registry listing and Redis Cloud UI

The Redis Cloud UI's **Integrate with → Pulumi** link opens the existing
[Redis Cloud package listing in the Pulumi Registry](https://www.pulumi.com/registry/packages/rediscloud/).
Publish the upcoming refresh through this existing package listing so that the UI
link continues to lead users to the provider. As reviewed on 12 November 2026,
the listing still displays v1.3.5, published on 20 December 2023.

Before announcing the new release, verify that this listing shows the released
version, updated installation instructions, and matching API documentation.
These unreleased notes do not mean the refreshed provider has been published.

## Changes

Compared with v1.3.5:

- Pulumi Terraform Bridge v3.60.1 is now v3.142.0.
- Terraform provider v1.3.1 is now v2.19.3. The Go require line is the pseudo-version of that tag, because the module path has no `/v2` suffix.
- Resources go from 11 to 27. Data sources go from 11 to 29.
- Pull requests run the `ci-success` check. The nightly QA suite is not a required check, and it refuses the production API host.
- A manual build can produce the provider and the Node.js, Python, Go, and .NET SDKs without publishing. The tag workflow uses GoReleaser v2 with `--clean`. Java is not published. NuGet stays unpublished.

These behavior changes make this a new major even where the tokens stay the same:

- `payment_method` is ignored after create.
- `REDISCLOUD_ACCESS_KEY` is the API key environment variable. `REDISCLOUD_API_KEY` still works when `REDISCLOUD_ACCESS_KEY` is unset.
- The database has `redis_version`.
- Terraform defaults apply for `auto_minor_version_upgrade`, `source_ips`, and `enable_default_user`.

Java is not in this refresh.
