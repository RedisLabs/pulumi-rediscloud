# Releasing the provider

A provider release is a git tag of the form `vX.Y.Z` pushed to this repository.
That push runs [`.github/workflows/release.yaml`](.github/workflows/release.yaml).

The workflow publishes:

- the GitHub release, through GoReleaser
- the npm package `@rediscloud/pulumi-rediscloud`
- the PyPI package `pulumi_rediscloud`

npm reads the Actions secret `NPM_TOKEN`. PyPI reads the Actions secret
`PYPI_TOKEN`. This repository does not store either value.

Java stays unpublished. `JAVA_PUBLISH` is `false`, and the publish matrix does
not include Java. NuGet stays unpublished. `NUGET_PUBLISH` is `false`. The
workflow still builds the Go and .NET SDKs, and it does not push those builds
to a package registry.

## Tags that are not a provider release

Tags under `sdk/` are not provider releases. GoReleaser ignores `sdk/*`, and
`release.yaml` triggers only on tags matching `v*.*.*`. An `sdk/vX.Y.Z` tag,
including `sdk/v1.3.5`, does not publish the provider, npm, or PyPI.

The release workflow creates `sdk/<version>` at the same commit after the
provider publish. That tag points at the SDK sources. Pushing it does not start
another provider release.

## What a release does not do

A provider release does not run the QA nightly acceptance workflow and does not
create a Redis Cloud subscription. Publishing Java or NuGet requires a separate
change to the flags in `release.yaml`.
