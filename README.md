# Redis Cloud Resource Provider

The Redis Cloud Resource Provider lets you manage [Redis Cloud](https://redislabs.com/redis-enterprise-cloud/overview) resources. The provider is used to interact with the resources supported by Redis Enterprise Cloud. It covers Pro (Flexible) and Annual subscriptions, Essentials (Fixed and Free) plans, Active-Active, ACL, cloud accounts, private service connect, private link, and transit gateway attachments. The schema matches `terraform-provider-rediscloud` v2.19.3.

## Installing

This package is available for several languages/platforms:

### Node.js (JavaScript/TypeScript)

To use from JavaScript or TypeScript in Node.js, install using either `npm`:

```bash
npm install @rediscloud/pulumi-rediscloud
```

or `yarn`:

```bash
yarn add @rediscloud/pulumi-rediscloud
```

### Python

To use from Python, install using `pip`:

```bash
pip install pulumi_rediscloud
```

### Go

To use from Go, use `go get` to grab the latest version of the library:

```bash
go get github.com/RedisLabs/pulumi-rediscloud/sdk/go/...
```

## Configuration

The following configuration points are available for the `rediscloud` provider:

- `apiKey` (environment: `REDISCLOUD_ACCESS_KEY`, then `REDISCLOUD_API_KEY`) - This is the Redis Enterprise Cloud API account key. `REDISCLOUD_API_KEY` still works when `REDISCLOUD_ACCESS_KEY` is unset.
- `secretKey` (environment: `REDISCLOUD_SECRET_KEY`) - This is the Redis Enterprise Cloud API secret key. It must be provided but can also be set by the environment variable.
- `url` (environment: `REDISCLOUD_URL`) - Optional Cloud API base URL. Defaults to the production Cloud API when unset.

## Usage

See [USAGE.md](USAGE.md) for a complete quickstart that configures credentials,
creates a Pro subscription and database, explains which Pulumi command triggers
Cloud API operations, and tears the resources down safely.

## Running the live QA acceptance workflow

The [`QA nightly acceptance`](.github/workflows/qa-live.yaml) workflow tests the
provider against a non-production Redis Cloud account. It creates an ACL rule,
one Pro subscription, and one database through Pulumi, waits for the cloud
resources to become active, and then destroys them. The final checks require the
subscription and database to return HTTP 404.

The workflow runs nightly and can also be started manually. It is not a pull
request check and does not block merges.

### Prerequisite

Add a repository Actions secret named `REDISCLOUD_QA`. Its value is a JSON
object containing credentials and the Cloud API URL for a QA account:

```json
{
  "api_key": "<qa-account-api-key>",
  "secret_key": "<qa-account-secret-key>",
  "url": "https://<qa-cloud-api-host>/v1"
}
```

The URL is required. The runner refuses the production
`api.redislabs.com` host and any of its subdomains. Never commit this JSON or
print it in logs.

### Run from the GitHub UI

1. Open **Actions** in this repository.
2. Select **QA nightly acceptance**.
3. Select **Run workflow** and use the `main` branch.
4. Choose `AWS` or `GCP`.
5. Enter a region, or leave it blank to use `us-east-1` for AWS or
   `us-central1` for GCP.
6. Set **Hold active resources for evidence capture** to `0` for a normal run,
   or up to `1800` seconds when screenshots are required.
7. Start the workflow and follow the **QA create and delete** job.

### Run with the GitHub CLI

AWS example:

```bash
gh workflow run qa-live.yaml \
  --repo RedisLabs/pulumi-rediscloud \
  --ref main \
  -f cloud_provider=AWS \
  -f region=us-east-1 \
  -f evidence_hold_seconds=300
```

GCP example:

```bash
gh workflow run qa-live.yaml \
  --repo RedisLabs/pulumi-rediscloud \
  --ref main \
  -f cloud_provider=GCP \
  -f region=us-central1 \
  -f evidence_hold_seconds=300
```

Find the new run and watch it:

```bash
gh run list \
  --repo RedisLabs/pulumi-rediscloud \
  --workflow qa-live.yaml \
  --limit 1

gh run watch <run-id> \
  --repo RedisLabs/pulumi-rediscloud
```

### Capture evidence

Every resource is named `pulumi-ci-<run-id>`. During the optional hold:

1. Find `active evidence checkpoint` in the workflow log. It includes the
   subscription ID, database ID, cloud provider, and region.
2. Open that subscription and database in the Redis Cloud SM UI.
3. Capture the workflow trigger and target, the active subscription, the active
   database, and the provider/region.
4. After the run finishes, capture the successful destroy and the database and
   subscription HTTP 404 checks.

The cleanup step runs even when an earlier workflow step fails. A later run also
removes leftover subscriptions whose names start with `pulumi-ci-` before it
creates new resources.

The AWS and GCP acceptance proof for this workflow is recorded in
[RED-225329](https://redislabs.atlassian.net/browse/RED-225329).

## Reference

For detailed reference documentation, please visit [the Pulumi registry](https://www.pulumi.com/registry/packages/rediscloud/api-docs/).

Repository vocabulary is in [GLOSSARY.md](GLOSSARY.md).
