package main

import (
	"fmt"

	"github.com/RedisLabs/pulumi-rediscloud/sdk/go/rediscloud"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi/config"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		cfg := config.New(ctx, "")
		name := cfg.Require("name")
		cidr := cfg.Require("cidr")
		includeDatabase := true
		if cfg.Get("includeDatabase") != "" {
			includeDatabase = cfg.GetBool("includeDatabase")
		}

		card, err := rediscloud.GetPaymentMethod(ctx, &rediscloud.GetPaymentMethodArgs{
			ExcludeExpired: pulumi.BoolRef(true),
		}, nil)
		if err != nil {
			return err
		}
		if card == nil || card.Id == "" {
			return fmt.Errorf("payment method lookup returned nothing")
		}

		regions, err := rediscloud.GetRegions(ctx, &rediscloud.GetRegionsArgs{
			ProviderName: pulumi.StringRef("AWS"),
		}, nil)
		if err != nil {
			return err
		}
		if regions == nil {
			return fmt.Errorf("regions lookup returned nothing")
		}

		plan, err := rediscloud.GetEssentialsPlan(ctx, &rediscloud.GetEssentialsPlanArgs{
			CloudProvider:          pulumi.StringRef("GCP"),
			Region:                 pulumi.StringRef("us-central1"),
			Name:                   pulumi.StringRef("1GB"),
			Size:                   pulumi.Float64Ref(1),
			SizeMeasurementUnit:    pulumi.StringRef("GB"),
			SupportReplication:     pulumi.BoolRef(false),
			SupportDataPersistence: pulumi.BoolRef(false),
		}, nil)
		if err != nil {
			return err
		}
		if plan == nil {
			return fmt.Errorf("essentials plan lookup returned nothing")
		}

		_, err = rediscloud.NewAclRule(ctx, "rule", &rediscloud.AclRuleArgs{
			Name: pulumi.String(name),
			Rule: pulumi.String("+@read ~*"),
		})
		if err != nil {
			return err
		}

		subscription, err := rediscloud.NewSubscription(ctx, "subscription", &rediscloud.SubscriptionArgs{
			Name:            pulumi.String(name),
			PaymentMethod:   pulumi.String("credit-card"),
			PaymentMethodId: pulumi.String(card.Id),
			MemoryStorage:   pulumi.String("ram"),
			CloudProvider: &rediscloud.SubscriptionCloudProviderArgs{
				Provider: pulumi.String("AWS"),
				Regions: rediscloud.SubscriptionCloudProviderRegionArray{
					&rediscloud.SubscriptionCloudProviderRegionArgs{
						Region:                     pulumi.String("us-east-1"),
						MultipleAvailabilityZones:  pulumi.Bool(false),
						NetworkingDeploymentCidr:   pulumi.String(cidr),
						PreferredAvailabilityZones: pulumi.StringArray{},
					},
				},
			},
			CreationPlan: &rediscloud.SubscriptionCreationPlanArgs{
				DatasetSizeInGb:            pulumi.Float64(1),
				Quantity:                   pulumi.Int(1),
				Replication:                pulumi.Bool(true),
				ThroughputMeasurementBy:    pulumi.String("operations-per-second"),
				ThroughputMeasurementValue: pulumi.Int(1000),
			},
		})
		if err != nil {
			return err
		}
		ctx.Export("subscriptionId", subscription.ID())

		if !includeDatabase {
			return nil
		}

		database, err := rediscloud.NewSubscriptionDatabase(ctx, "database", &rediscloud.SubscriptionDatabaseArgs{
			Name:                       pulumi.String(name),
			SubscriptionId:             subscription.ID(),
			Protocol:                   pulumi.String("redis"),
			DatasetSizeInGb:            pulumi.Float64(1),
			DataPersistence:            pulumi.String("none"),
			ThroughputMeasurementBy:    pulumi.String("operations-per-second"),
			ThroughputMeasurementValue: pulumi.Int(1000),
			Replication:                pulumi.Bool(true),
		})
		if err != nil {
			return err
		}
		ctx.Export("databaseId", database.DbId)
		ctx.Export("publicEndpoint", database.PublicEndpoint)
		ctx.Export("privateEndpoint", database.PrivateEndpoint)
		return nil
	})
}
