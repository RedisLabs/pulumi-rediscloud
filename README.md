# Redis Cloud Resource Provider

The Redis Cloud Resource Provider lets you manage [Redis Cloud](https://redislabs.com/redis-enterprise-cloud/overview) resources.

## Installing

This package is available for several languages/platforms:

### Node.js (JavaScript/TypeScript)

To use from JavaScript or TypeScript in Node.js, install using either `npm`:

```bash
npm install @RedisLabs/pulumi-rediscloud
```

or `yarn`:

```bash
yarn add @RedisLabs/pulumi-rediscloud
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

### .NET

To use from .NET, install using `dotnet add package`:

```bash
dotnet add package RedisLabs.PulumiRedisCloud
```

## Configuration

The following configuration points are available for the `rediscloud` provider:

- `apiKey` (environment: `REDISCLOUD_ACCESS_KEY`) - This is the Redis Enterprise Cloud API account key. It must be provided but can also be set by the environment variable.
- `secretKey` (environment: `REDISCLOUD_SECRET_KEY`) - This is the Redis Enterprise Cloud API secret key. It must be provided but can also be set by the environment variable.

## Reference

For detailed reference documentation, please visit [the Pulumi registry](https://www.pulumi.com/registry/packages/rediscloud/api-docs/).
