# Using the Redis Cloud Pulumi provider

This guide creates a Redis Cloud Pro subscription and database with the
JavaScript SDK. The same provider is available for TypeScript, Python, Go,
.NET, and Pulumi YAML; sample projects for those runtimes are in
[`examples/`](examples/).

Creating these resources can incur Redis Cloud charges. Run the example in the
account and region you intend to use, and destroy the stack when it is no
longer needed.

## Prerequisites

- A [Pulumi CLI](https://www.pulumi.com/docs/iac/download-install/) installation
- Node.js 20 or later
- A Redis Cloud account with an API account key and secret key
- A payment method configured in that Redis Cloud account

Create API keys in the Redis Cloud console under **Access Management** >
**API Keys**. The account key needs permission to manage the resources in the
program.

## Create a project

Create an empty directory and add these two files.

`Pulumi.yaml`:

```yaml
name: rediscloud-quickstart
runtime:
  name: nodejs
  options:
    typescript: false
description: Redis Cloud provider quickstart
```

`index.js`:

```javascript
import rediscloud from "@rediscloud/pulumi-rediscloud";

const paymentMethod = await rediscloud.getPaymentMethod({
  excludeExpired: true,
});

const subscription = new rediscloud.Subscription("quickstart-subscription", {
  name: "pulumi-quickstart",
  paymentMethod: "credit-card",
  paymentMethodId: paymentMethod.id,
  memoryStorage: "ram",
  cloudProvider: {
    provider: "AWS",
    regions: [{
      region: "us-east-1",
      multipleAvailabilityZones: false,
      networkingDeploymentCidr: "10.0.0.0/24",
    }],
  },
  creationPlan: {
    memoryLimitInGb: 1,
    quantity: 1,
    replication: true,
    throughputMeasurementBy: "operations-per-second",
    throughputMeasurementValue: 1000,
  },
});

const database = new rediscloud.SubscriptionDatabase("quickstart-database", {
  name: "pulumi-quickstart",
  subscriptionId: subscription.id,
  protocol: "redis",
  memoryLimitInGb: 1,
  dataPersistence: "none",
  throughputMeasurementBy: "operations-per-second",
  throughputMeasurementValue: 1000,
  replication: true,
});

export const subscriptionId = subscription.id;
export const databaseId = database.dbId;
export const publicEndpoint = database.publicEndpoint;
```

Initialize the Node.js project and install the Pulumi SDKs:

```bash
npm init -y
npm pkg set type=module
npm install @pulumi/pulumi @rediscloud/pulumi-rediscloud
```

## Configure credentials

The provider reads Redis Cloud credentials from the environment:

```bash
export REDISCLOUD_ACCESS_KEY="<account-key>"
export REDISCLOUD_SECRET_KEY="<secret-key>"
```

`REDISCLOUD_API_KEY` remains supported as a fallback when
`REDISCLOUD_ACCESS_KEY` is unset. To use a non-production Cloud API endpoint,
also set its complete v1 base URL:

```bash
export REDISCLOUD_URL="https://<cloud-api-host>/v1"
```

When `REDISCLOUD_URL` is unset, the provider uses
`https://api.redislabs.com/v1`.

## Preview and create the resources

Log in to a Pulumi backend and create a stack if the project does not have one:

```bash
pulumi login
pulumi stack init dev
```

Preview the plan:

```bash
pulumi preview
```

`pulumi preview` loads `pulumi-resource-rediscloud` and may make read-only Cloud
API calls for data-source lookups, such as `getPaymentMethod`. It does not
create the subscription or database.

Apply the plan:

```bash
pulumi up
```

`pulumi up` is the command that triggers the provider's create, read, update,
and delete operations. The provider translates those operations through the
Terraform bridge, and the wrapped Redis Cloud Terraform provider sends the
corresponding requests to the Cloud API.

After the update completes, inspect the IDs and endpoint:

```bash
pulumi stack output
```

The subscription and database also appear in the Redis Cloud console for the
account selected by the credentials.

## Use GCP instead of AWS

Change the `cloudProvider` block in `index.js`:

```javascript
cloudProvider: {
  provider: "GCP",
  regions: [{
    region: "us-central1",
    multipleAvailabilityZones: false,
    networkingDeploymentCidr: "10.0.0.0/24",
  }],
},
```

Use a CIDR that does not overlap networks you plan to peer with. Available
regions and capabilities depend on the Redis Cloud account and plan.

## Update and delete the stack

Edit the program and run `pulumi preview` followed by `pulumi up` to apply an
update. To delete every resource managed by this stack, run:

```bash
pulumi destroy
```

Confirm the destroy, then remove the empty stack if it is no longer needed:

```bash
pulumi stack rm dev
```

## Other languages and resources

- [JavaScript example](examples/nodejs/)
- [Python example](examples/python/)
- [Go example](examples/go/)
- [.NET example](examples/dotnet/)
- [Pulumi YAML example](examples/yaml/)
- [Provider API reference](https://www.pulumi.com/registry/packages/rediscloud/api-docs/)
- [Live AWS and GCP acceptance workflow](README.md#running-the-live-qa-acceptance-workflow)

The provider supports Pro, Essentials, Active-Active, ACL, cloud-account, and
networking resources. Consult the API reference for each resource's required
properties and outputs.
