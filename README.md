# Redis Cloud Resource Provider

The Redis Cloud Resource Provider lets you manage [Redis Cloud](https://redislabs.com/redis-enterprise-cloud/overview) resources. The provider is used to interact with the resources supported by Redis Enterprise Cloud. It covers Pro (Flexible) and Annual subscriptions, Essentials (Fixed and Free) plans, Active-Active, ACL, cloud accounts, private connectivity, and transit gateway attachments. The schema matches `terraform-provider-rediscloud` v2.19.3.

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

## Reference

For detailed reference documentation, please visit [the Pulumi registry](https://www.pulumi.com/registry/packages/rediscloud/api-docs/).

Repository vocabulary is in [GLOSSARY.md](GLOSSARY.md).
