# Unreleased

Do not tag this refresh. v1.3.5 remains the latest installable release until a later decision tags v2.0.0.

Compared with v1.3.5:

- Pulumi Terraform Bridge v3.60.1 is now v3.142.0.
- Terraform provider v1.3.1 is now v2.19.3. The Go require line is the pseudo-version of that tag, because the module path has no `/v2` suffix.
- Resources go from 11 to 27. Data sources go from 11 to 29.
- Pull requests run the `ci-success` check. The nightly QA suite is not a required check, and it refuses the production API host.
- A manual build can produce the provider and the Node.js, Python, Go, and .NET SDKs without publishing. The tag workflow uses GoReleaser v2 with `--clean`. Java is not published. NuGet stays unpublished.

These behavior changes make this a new major even where the tokens stay the same:

- `payment_method` is ignored after create.
- The database has `redis_version`.
- Terraform defaults apply for `auto_minor_version_upgrade`, `source_ips`, and `enable_default_user`.

Java is not in this refresh.
