"use strict";
import pulumi from "@pulumi/pulumi";
import rediscloud from "@rediscloud/pulumi-rediscloud";

const config = new pulumi.Config();

const redisCloudProvider = new rediscloud.Provider("rediscloud", {});

const card = await rediscloud.getPaymentMethod(
	{
		cardType: "Visa",
		lastFourNumbers: "3209",
	},
	{
		provider: redisCloudProvider,
	},
);

const subscription = new rediscloud.Subscription(
	"one",
	{
		name: "one",
		paymentMethod: "credit-card",
		paymentMethodId: card.id,


		cloudProvider: {
			regions: [
				{
					region: "eu-west-2",
					multipleAvailabilityZones: false,
					networkingDeploymentCidr: "10.0.0.0/24",
					preferredAvailabilityZones: ["euw2-az1"],
				},
			],
		},

		creationPlan: {
			averageItemSizeInBytes: 1,
			memoryLimitInGb: 2,
			quantity: 1,
			replication: false,
			supportOssClusterApi: false,
			throughputMeasurementBy: "operations-per-second",
			throughputMeasurementValue: 10000,
			modules: [],
		},
	},
	{
		provider: redisCloudProvider,
	},
);

const database = new rediscloud.SubscriptionDatabase("one", {
	name: "one",
	subscriptionId: subscription.id,
	protocol: "redis",

	memoryLimitInGb: 1,
	dataPersistence: "none",
	throughputMeasurementBy: "operations-per-second",
	throughputMeasurementValue: 10000,
	supportOssClusterApi: false,
	externalEndpointForOssClusterApi: false,
	replication: true,
}, {
	provider: redisCloudProvider,
});
