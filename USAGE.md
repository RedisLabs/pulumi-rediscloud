# Using the Redis Cloud Pulumi provider

This guide creates a Redis Cloud Pro subscription and database with the
JavaScript SDK. The same provider is available for TypeScript, Python, Go,
.NET, and Pulumi YAML; sample projects for those runtimes are in
[`examples/`](examples/). [Shipped resources](#shipped-resources) then covers
every resource in the v2.20.0 schema. Values in the later examples are
synthetic.

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

## Shipped resources

The snippets below continue the quickstart `index.js`. They use the
`paymentMethod`, `subscription`, and `database` values already declared there.
Each block names the Pulumi resource and sets the arguments
`schema.json` lists in `requiredInputs`, including required fields nested
inside those arguments. Optional arguments appear only when the schema's own
description makes them part of a normal create, or when a later lookup needs
them. Values are synthetic. The snippets do not contain account IDs, hosts, or
credentials.

Add this import next to the quickstart import. The config values are supplied
outside the program and are not written here.

```javascript
import * as pulumi from "@pulumi/pulumi";

const exampleConfig = new pulumi.Config();
```

The schema says an ACL user password must contain a lower-case letter, an
upper-case letter, a number, and a special character. Put that value in Pulumi
config under `exampleAclUserPassword`.

### Subscription and SubscriptionDatabase

`Subscription` requires `cloudProvider`, and each `cloudProvider.regions` entry
requires `region` and `networkingDeploymentCidr`. `SubscriptionDatabase`
requires `subscriptionId`, `throughputMeasurementBy`, and
`throughputMeasurementValue`.

The [quickstart program](#create-a-project) sets those arguments. The same two
resources, with the same required arguments, are in
[examples/nodejs/index.js](examples/nodejs/index.js),
[examples/python/\_\_main\_\_.py](examples/python/__main__.py),
[examples/go/main.go](examples/go/main.go), and
[examples/yaml/Pulumi.yaml](examples/yaml/Pulumi.yaml).

### AclRule, AclRole, and AclUser

`AclRule` requires `rule`. `AclRole` requires `rules`, and each rule requires
`name` and `databases`. Each database entry requires `database` and
`subscription`. `AclUser` requires `password` and `role`.

```javascript
const aclRule = new rediscloud.AclRule("example-acl-rule", {
  name: "example-rule",
  rule: "+@read ~example:*",
});

const aclRole = new rediscloud.AclRole("example-acl-role", {
  name: "example-role",
  rules: [{
    name: aclRule.name,
    databases: [{
      subscription: subscription.id.apply(id => Number(id)),
      database: database.dbId,
    }],
  }],
});

const aclUser = new rediscloud.AclUser("example-acl-user", {
  name: "example-user",
  role: aclRole.name,
  password: exampleConfig.requireSecret("exampleAclUserPassword"),
});
```

`database` and `subscription` on the role are integers in the schema.
`subscription.id` is a string, so the example converts it. `database.dbId` is
already an integer.

### EssentialsSubscription and EssentialsDatabase

`EssentialsSubscription` requires `planId`. `EssentialsDatabase` requires
`subscriptionId`, `dataPersistence`, and `replication`. `planId` and the
Essentials `subscriptionId` are integers. `getEssentialsPlan` and
`getPaymentMethod` have no required inputs. The plan filters below are the
schema's documented example filters. `paymentMethodId` is optional in the
schema and is an integer; the schema says a paid plan needs a payment method
defined in the account.

```javascript
const essentialsPlan = await rediscloud.getEssentialsPlan({
  name: "Single-Zone_1GB",
  cloudProvider: "AWS",
  region: "us-west-1",
});

const essentialsSubscription = new rediscloud.EssentialsSubscription("example-essentials-subscription", {
  name: "example-essentials",
  planId: essentialsPlan.id,
  paymentMethodId: pulumi.output(paymentMethod.id).apply(id => Number(id)),
});

const essentialsDatabase = new rediscloud.EssentialsDatabase("example-essentials-database", {
  name: "example-essentials",
  subscriptionId: essentialsSubscription.id.apply(id => Number(id)),
  dataPersistence: "none",
  replication: false,
});
```

### ActiveActiveSubscription and ActiveActiveSubscriptionDatabase

`ActiveActiveSubscription` has no `requiredInputs`. The schema says
`paymentMethodId` is optional for marketplace accounts and required for other
account types. This example sets it from `getPaymentMethod`. `creationPlan` is
optional; when it is set, the schema requires `quantity` and `regions`, and
each region requires `region`, `networkingDeploymentCidr`,
`readOperationsPerSecond`, and `writeOperationsPerSecond`.

`ActiveActiveSubscriptionDatabase` requires `subscriptionId`.

```javascript
const activeActiveSubscription = new rediscloud.ActiveActiveSubscription("example-active-active-subscription", {
  name: "example-active-active",
  cloudProvider: "AWS",
  paymentMethod: "credit-card",
  paymentMethodId: paymentMethod.id,
  creationPlan: {
    quantity: 1,
    regions: [
      {
        region: "us-east-1",
        networkingDeploymentCidr: "10.1.0.0/24",
        readOperationsPerSecond: 1000,
        writeOperationsPerSecond: 1000,
      },
      {
        region: "us-east-2",
        networkingDeploymentCidr: "10.1.1.0/24",
        readOperationsPerSecond: 1000,
        writeOperationsPerSecond: 1000,
      },
    ],
  },
});

const activeActiveDatabase = new rediscloud.ActiveActiveSubscriptionDatabase("example-active-active-database", {
  name: "example-active-active",
  subscriptionId: activeActiveSubscription.id,
});
```

### ActiveActiveSubscriptionRegions

`ActiveActiveSubscriptionRegions` requires `subscriptionId` and `regions`. Each
region requires `region`, `networkingDeploymentCidr`, and `databases`. Each
database entry requires `databaseId`, `databaseName`,
`localReadOperationsPerSecond`, and `localWriteOperationsPerSecond`. This
block is the example for that resource. The creation plan above already names
the same two regions, so this is not a second copy to apply on top of that
plan.

```javascript
const activeActiveRegions = new rediscloud.ActiveActiveSubscriptionRegions("example-active-active-regions", {
  subscriptionId: activeActiveSubscription.id,
  regions: [
    {
      region: "us-east-1",
      networkingDeploymentCidr: "10.1.0.0/24",
      databases: [{
        databaseId: activeActiveDatabase.dbId,
        databaseName: activeActiveDatabase.name,
        localReadOperationsPerSecond: 1000,
        localWriteOperationsPerSecond: 1000,
      }],
    },
    {
      region: "us-east-2",
      networkingDeploymentCidr: "10.1.1.0/24",
      databases: [{
        databaseId: activeActiveDatabase.dbId,
        databaseName: activeActiveDatabase.name,
        localReadOperationsPerSecond: 1000,
        localWriteOperationsPerSecond: 1000,
      }],
    },
  ],
});
```

### SubscriptionPeering and ActiveActiveSubscriptionPeering

`subscriptionId` is the only `requiredInputs` entry. The shipped AWS examples
in `sdk/go/rediscloud/subscriptionPeering.go` and
`sdk/go/rediscloud/activeActiveSubscriptionPeering.go` also set the
destination account, VPC, and region, and the schema says either `vpcCidr` or
`vpcCidrs` must be set. Read the account and VPC from config. The CIDRs below
are synthetic.

```javascript
const subscriptionPeering = new rediscloud.SubscriptionPeering("example-peering", {
  subscriptionId: subscription.id,
  region: "us-east-1",
  awsAccountId: exampleConfig.require("exampleAwsAccountId"),
  vpcId: exampleConfig.require("exampleVpcId"),
  vpcCidr: "10.0.30.0/24",
});

const activeActivePeering = new rediscloud.ActiveActiveSubscriptionPeering("example-active-active-peering", {
  subscriptionId: activeActiveSubscription.id,
  sourceRegion: "us-east-1",
  destinationRegion: "eu-west-2",
  awsAccountId: exampleConfig.require("exampleAwsAccountId"),
  vpcId: exampleConfig.require("exampleActiveActiveVpcId"),
  vpcCidr: "10.0.31.0/24",
});
```

### PrivateLink and ActiveActivePrivateLink

`PrivateLink` requires `subscriptionId`, `shareName`, and `principals`.
`ActiveActivePrivateLink` also requires `regionId`. Each principal requires
`principal` and `principalType`. The schema's JavaScript values for
`principalType` are `awsAccount`, `organization`, `organizationUnit`,
`iamRole`, `iamUser`, and `servicePrincipal`. This example uses
`servicePrincipal` and a synthetic principal name.

`getActiveActiveSubscriptionRegions` requires `subscriptionName`. Its `regionId`
output is an integer, which matches the Active-Active Private Link input.

```javascript
const activeActiveRegionLookup = rediscloud.getActiveActiveSubscriptionRegionsOutput({
  subscriptionName: activeActiveSubscription.name,
});

const privateLink = new rediscloud.PrivateLink("example-private-link", {
  subscriptionId: subscription.id,
  shareName: "example-share",
  principals: [{
    principal: "example-service",
    principalType: "servicePrincipal",
  }],
});

const activeActivePrivateLink = new rediscloud.ActiveActivePrivateLink("example-active-active-private-link", {
  subscriptionId: activeActiveSubscription.id,
  regionId: activeActiveRegionLookup.regions.apply(regions => regions[0].regionId),
  shareName: "example-active-active-share",
  principals: [{
    principal: "example-service",
    principalType: "servicePrincipal",
  }],
});
```

### Private Service Connect

Private Service Connect requires GCP. The quickstart `subscription` and the
earlier `activeActiveSubscription` are AWS. The shipped example in
`sdk/go/rediscloud/privateServiceConnectEndpoint.go` sets
`cloudProvider.provider` to `GCP`. The two subscriptions below are those
definitions adapted to GCP. For Active-Active, `cloudProvider` is the string
`GCP`.

`PrivateServiceConnect` requires `subscriptionId`.
`PrivateServiceConnectEndpoint` requires `subscriptionId`,
`privateServiceConnectServiceId`, `gcpProjectId`, `gcpVpcName`,
`gcpVpcSubnetName`, and `endpointConnectionName`.
`PrivateServiceConnectEndpointAccepter` requires `subscriptionId`,
`privateServiceConnectServiceId`, `privateServiceConnectEndpointId`, and
`action`. The schema accepts `accept` and `reject` for `action`.

The Active-Active service, endpoint, and accepter require those same arguments
plus `regionId`. `regionId` is an integer on these Private Service Connect
resources. On `ActiveActiveTransitGatewayAttachment` and
`ActiveActiveTransitGatewayRoute`, the schema types `regionId` as a string.

The shipped Go example says an endpoint can be accepted only after the GCP
forwarding rules exist, and the accepter depends on those rules. Create the
forwarding rule first, for both Pro and Active-Active, and pass it in
`dependsOn`. Project, network, subnet, and endpoint names below are synthetic.
Install `@pulumi/gcp` before running this section.

```javascript
import * as gcp from "@pulumi/gcp";

const gcpSubscription = new rediscloud.Subscription("example-gcp-subscription", {
  name: "example-gcp",
  paymentMethod: "credit-card",
  paymentMethodId: paymentMethod.id,
  cloudProvider: {
    provider: "GCP",
    regions: [{
      region: "us-central1",
      networkingDeploymentCidr: "10.2.0.0/24",
    }],
  },
  creationPlan: {
    quantity: 1,
    replication: true,
    throughputMeasurementBy: "operations-per-second",
    throughputMeasurementValue: 1000,
  },
});

const gcpActiveActiveSubscription = new rediscloud.ActiveActiveSubscription("example-gcp-active-active-subscription", {
  name: "example-gcp-active-active",
  cloudProvider: "GCP",
  paymentMethod: "credit-card",
  paymentMethodId: paymentMethod.id,
  creationPlan: {
    quantity: 1,
    regions: [
      {
        region: "us-central1",
        networkingDeploymentCidr: "10.2.1.0/24",
        readOperationsPerSecond: 1000,
        writeOperationsPerSecond: 1000,
      },
      {
        region: "us-east1",
        networkingDeploymentCidr: "10.2.2.0/24",
        readOperationsPerSecond: 1000,
        writeOperationsPerSecond: 1000,
      },
    ],
  },
});

const gcpActiveActiveRegionLookup = rediscloud.getActiveActiveSubscriptionRegionsOutput({
  subscriptionName: gcpActiveActiveSubscription.name,
});

const privateServiceConnect = new rediscloud.PrivateServiceConnect("example-private-service-connect", {
  subscriptionId: gcpSubscription.id,
});

const privateServiceConnectEndpoint = new rediscloud.PrivateServiceConnectEndpoint("example-private-service-connect-endpoint", {
  subscriptionId: gcpSubscription.id,
  privateServiceConnectServiceId: privateServiceConnect.privateServiceConnectServiceId,
  gcpProjectId: "example-project",
  gcpVpcName: "example-vpc",
  gcpVpcSubnetName: "example-subnet",
  endpointConnectionName: "example-endpoint",
});

const privateServiceConnectAddress = new gcp.compute.Address("example-psc-address", {
  project: "example-project",
  name: privateServiceConnectEndpoint.serviceAttachments.apply(attachments => attachments[0].ipAddressName),
  subnetwork: "example-subnet",
  addressType: "INTERNAL",
  region: "us-central1",
});

const privateServiceConnectForwardingRule = new gcp.compute.ForwardingRule("example-psc-forwarding-rule", {
  name: privateServiceConnectEndpoint.serviceAttachments.apply(attachments => attachments[0].forwardingRuleName),
  project: "example-project",
  region: "us-central1",
  ipAddress: privateServiceConnectAddress.id,
  network: "example-vpc",
  target: privateServiceConnectEndpoint.serviceAttachments.apply(attachments => attachments[0].name),
  loadBalancingScheme: "",
});

const privateServiceConnectEndpointAccepter = new rediscloud.PrivateServiceConnectEndpointAccepter("example-private-service-connect-accepter", {
  subscriptionId: gcpSubscription.id,
  privateServiceConnectServiceId: privateServiceConnect.privateServiceConnectServiceId,
  privateServiceConnectEndpointId: privateServiceConnectEndpoint.privateServiceConnectEndpointId,
  action: "accept",
}, { dependsOn: [privateServiceConnectForwardingRule] });

const activeActivePrivateServiceConnect = new rediscloud.ActiveActivePrivateServiceConnect("example-active-active-private-service-connect", {
  subscriptionId: gcpActiveActiveSubscription.id,
  regionId: gcpActiveActiveRegionLookup.regions.apply(regions => regions[0].regionId),
});

const activeActivePrivateServiceConnectEndpoint = new rediscloud.ActiveActivePrivateServiceConnectEndpoint("example-active-active-private-service-connect-endpoint", {
  subscriptionId: gcpActiveActiveSubscription.id,
  regionId: gcpActiveActiveRegionLookup.regions.apply(regions => regions[0].regionId),
  privateServiceConnectServiceId: activeActivePrivateServiceConnect.privateServiceConnectServiceId,
  gcpProjectId: "example-project",
  gcpVpcName: "example-vpc",
  gcpVpcSubnetName: "example-subnet",
  endpointConnectionName: "example-endpoint",
});

const activeActivePrivateServiceConnectAddress = new gcp.compute.Address("example-active-active-psc-address", {
  project: "example-project",
  name: activeActivePrivateServiceConnectEndpoint.serviceAttachments.apply(attachments => attachments[0].ipAddressName),
  subnetwork: "example-subnet",
  addressType: "INTERNAL",
  region: "us-central1",
});

const activeActivePrivateServiceConnectForwardingRule = new gcp.compute.ForwardingRule("example-active-active-psc-forwarding-rule", {
  name: activeActivePrivateServiceConnectEndpoint.serviceAttachments.apply(attachments => attachments[0].forwardingRuleName),
  project: "example-project",
  region: "us-central1",
  ipAddress: activeActivePrivateServiceConnectAddress.id,
  network: "example-vpc",
  target: activeActivePrivateServiceConnectEndpoint.serviceAttachments.apply(attachments => attachments[0].name),
  loadBalancingScheme: "",
});

const activeActivePrivateServiceConnectEndpointAccepter = new rediscloud.ActiveActivePrivateServiceConnectEndpointAccepter("example-active-active-private-service-connect-accepter", {
  subscriptionId: gcpActiveActiveSubscription.id,
  regionId: gcpActiveActiveRegionLookup.regions.apply(regions => regions[0].regionId),
  privateServiceConnectServiceId: activeActivePrivateServiceConnect.privateServiceConnectServiceId,
  privateServiceConnectEndpointId: activeActivePrivateServiceConnectEndpoint.privateServiceConnectEndpointId,
  action: "accept",
}, { dependsOn: [activeActivePrivateServiceConnectForwardingRule] });
```

### Transit gateway

`TransitGatewayInvitationAcceptor` requires `subscriptionId`,
`tgwInvitationId`, and `action`. `TransitGatewayAttachment` requires
`subscriptionId` and `tgwId`. `TransitGatewayRoute` requires `subscriptionId`,
`tgwId`, and `cidrs`.

`getTransitGatewayInvitations` and `getTransitGateway` require
`subscriptionId`. The Active-Active lookups also require `regionId`.
`ActiveActiveTransitGatewayInvitationAcceptor` requires `subscriptionId`,
`regionId`, `tgwInvitationId`, and `action`.
`ActiveActiveTransitGatewayAttachment` and `ActiveActiveTransitGatewayRoute`
require `subscriptionId`, `regionId`, and `tgwId`. The route also requires
`cidrs`. `action` accepts `accept` and `reject`.

`sdk/go/rediscloud/transitGatewayRoute.go` and
`sdk/go/rediscloud/activeActiveTransitGatewayRoute.go` say to configure CIDRs
only after the attachment is accepted on both Redis Cloud and AWS, and to use
`dependsOn`. Accept the invitation, create the attachment, accept it on AWS,
and make the route wait for both acceptances. Install `@pulumi/aws` before
running this section. These resources stay on the AWS subscriptions above.

```javascript
import * as aws from "@pulumi/aws";

const transitGatewayInvitations = rediscloud.getTransitGatewayInvitationsOutput({
  subscriptionId: subscription.id,
});

const transitGatewayInvitationAcceptor = new rediscloud.TransitGatewayInvitationAcceptor("example-transit-gateway-invitation", {
  subscriptionId: subscription.id,
  tgwInvitationId: transitGatewayInvitations.invitations.apply(invitations => invitations[0].id),
  action: "accept",
});

const transitGateway = rediscloud.getTransitGatewayOutput({
  subscriptionId: subscription.id,
});

const transitGatewayAttachment = new rediscloud.TransitGatewayAttachment("example-transit-gateway-attachment", {
  subscriptionId: subscription.id,
  tgwId: transitGateway.tgwId,
});

const transitGatewayAttachmentAccepter = new aws.ec2transitgateway.VpcAttachmentAccepter("example-transit-gateway-attachment-accepter", {
  transitGatewayAttachmentId: transitGatewayAttachment.attachmentUid,
});

const transitGatewayRoute = new rediscloud.TransitGatewayRoute("example-transit-gateway-route", {
  subscriptionId: subscription.id,
  tgwId: transitGateway.tgwId,
  cidrs: ["10.0.20.0/24"],
}, { dependsOn: [transitGatewayInvitationAcceptor, transitGatewayAttachmentAccepter] });

const activeActiveTransitGatewayInvitations = rediscloud.getActiveActiveTransitGatewayInvitationsOutput({
  subscriptionId: activeActiveSubscription.id,
  regionId: activeActiveRegionLookup.regions.apply(regions => regions[0].regionId),
});

const activeActiveTransitGatewayInvitationAcceptor = new rediscloud.ActiveActiveTransitGatewayInvitationAcceptor("example-active-active-transit-gateway-invitation", {
  subscriptionId: activeActiveSubscription.id,
  regionId: activeActiveRegionLookup.regions.apply(regions => regions[0].regionId),
  tgwInvitationId: activeActiveTransitGatewayInvitations.invitations.apply(invitations => invitations[0].id),
  action: "accept",
});

const activeActiveTransitGateway = rediscloud.getActiveActiveTransitGatewayOutput({
  subscriptionId: activeActiveSubscription.id,
  regionId: activeActiveRegionLookup.regions.apply(regions => regions[0].regionId),
});

const activeActiveRegionId = activeActiveRegionLookup.regions.apply(regions => String(regions[0].regionId));

const activeActiveTransitGatewayAttachment = new rediscloud.ActiveActiveTransitGatewayAttachment("example-active-active-transit-gateway-attachment", {
  subscriptionId: activeActiveSubscription.id,
  regionId: activeActiveRegionId,
  tgwId: activeActiveTransitGateway.tgwId,
});

const activeActiveTransitGatewayAttachmentAccepter = new aws.ec2transitgateway.VpcAttachmentAccepter("example-active-active-transit-gateway-attachment-accepter", {
  transitGatewayAttachmentId: activeActiveTransitGatewayAttachment.attachmentUid,
});

const activeActiveTransitGatewayRoute = new rediscloud.ActiveActiveTransitGatewayRoute("example-active-active-transit-gateway-route", {
  subscriptionId: activeActiveSubscription.id,
  regionId: activeActiveRegionId,
  tgwId: activeActiveTransitGateway.tgwId,
  cidrs: ["10.0.21.0/24"],
}, { dependsOn: [activeActiveTransitGatewayInvitationAcceptor, activeActiveTransitGatewayAttachmentAccepter] });
```

### CloudAccount

`CloudAccount` requires `accessKeyId`, `accessSecretKey`, `consoleUsername`,
`consolePassword`, `providerType`, and `signInLoginUrl`. `providerType` is
`AWS` or `GCP`. The key, password, and console login URL are read from config
so this page does not contain credentials or a host.

```javascript
const cloudAccount = new rediscloud.CloudAccount("example-cloud-account", {
  accessKeyId: exampleConfig.require("exampleAccessKeyId"),
  accessSecretKey: exampleConfig.requireSecret("exampleAccessSecretKey"),
  consoleUsername: "example-console-user",
  consolePassword: exampleConfig.requireSecret("exampleConsolePassword"),
  providerType: "AWS",
  signInLoginUrl: exampleConfig.require("exampleSignInLoginUrl"),
});
```

### AgentMemory and AgentMemoryApiKey

`AgentMemory` requires `databaseId`, an integer. The schema's minimal example
uses the Pro database `dbId`. `AgentMemoryApiKey` requires `storeId`. The
generated API key is an output. This example does not print it.

```javascript
const agentMemory = new rediscloud.AgentMemory("example-agent-memory", {
  name: "example-memory",
  databaseId: database.dbId,
});

const agentMemoryApiKey = new rediscloud.AgentMemoryApiKey("example-agent-memory-api-key", {
  name: "example-application",
  storeId: agentMemory.id,
});
```

## Other languages and resources

- [JavaScript example](examples/nodejs/)
- [Python example](examples/python/)
- [Go example](examples/go/)
- [.NET example](examples/dotnet/)
- [Pulumi YAML example](examples/yaml/)
- [Provider API reference](https://www.pulumi.com/registry/packages/rediscloud/api-docs/)
- [Live AWS and GCP acceptance workflow](README.md#running-the-live-qa-acceptance-workflow)
- [Provider release](RELEASE.md)

