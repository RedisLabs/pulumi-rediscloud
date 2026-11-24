package main

import (
	"fmt"
	"strconv"

	"github.com/RedisLabs/pulumi-rediscloud/sdk/go/rediscloud"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

// createEssentials registers resources only; the caller must provide a plan and
// payment method returned by authenticated Cloud lookups.
func createEssentials(ctx *pulumi.Context, name string, planID int, paymentID string, includeDatabase bool) error {
	card, err := strconv.Atoi(paymentID)
	if err != nil || card <= 0 || planID <= 0 || name == "" {
		return fmt.Errorf("Essentials name, plan and payment method must be valid")
	}
	sub, err := rediscloud.NewEssentialsSubscription(ctx, "essentials-subscription", &rediscloud.EssentialsSubscriptionArgs{
		Name: pulumi.String(name), PlanId: pulumi.Int(planID),
		PaymentMethod: pulumi.String("credit-card"), PaymentMethodId: pulumi.Int(card),
	})
	if err != nil {
		return err
	}
	ctx.Export("essentialsSubscriptionId", sub.ID())
	if !includeDatabase {
		return nil
	}
	db, err := rediscloud.NewEssentialsDatabase(ctx, "essentials-database", &rediscloud.EssentialsDatabaseArgs{
		Name: pulumi.String(name),
		SubscriptionId: sub.ID().ToStringOutput().ApplyT(func(id string) (int, error) {
			parsed, parseErr := strconv.Atoi(id)
			if parseErr != nil || parsed <= 0 {
				return 0, fmt.Errorf("Essentials subscription ID is invalid")
			}
			return parsed, nil
		}).(pulumi.IntOutput),
		DataPersistence: pulumi.String("none"), Replication: pulumi.Bool(false),
	})
	if err != nil {
		return err
	}
	ctx.Export("essentialsDatabaseId", db.DbId)
	ctx.Export("publicEndpoint", db.PublicEndpoint)
	ctx.Export("privateEndpoint", db.PrivateEndpoint)
	return nil
}
