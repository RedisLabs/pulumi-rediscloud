// A Pulumi program used only by the isolated loopback provider test.
package main

import (
	"fmt"
	"strconv"

	"github.com/RedisLabs/pulumi-rediscloud/sdk/go/rediscloud"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi/config"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		cfg := config.New(ctx, "")
		sub, err := rediscloud.NewEssentialsSubscription(ctx, "sub", &rediscloud.EssentialsSubscriptionArgs{
			Name: pulumi.String("fixture"), PlanId: pulumi.Int(7), PaymentMethod: pulumi.String("credit-card"), PaymentMethodId: pulumi.Int(3),
		})
		if err != nil {
			return err
		}
		ctx.Export("sub", sub.ID())
		if !cfg.GetBool("includeDatabase") {
			return nil
		}
		eviction := cfg.Get("eviction")
		if eviction == "" {
			eviction = "volatile-lru"
		}
		db, err := rediscloud.NewEssentialsDatabase(ctx, "db", &rediscloud.EssentialsDatabaseArgs{
			Name: pulumi.String("fixture"), DataPersistence: pulumi.String("none"), DataEviction: pulumi.String(eviction), Replication: pulumi.Bool(false),
			SubscriptionId: sub.ID().ToStringOutput().ApplyT(func(id string) (int, error) {
				v, parseErr := strconv.Atoi(id)
				if parseErr != nil || v <= 0 {
					return 0, fmt.Errorf("invalid fixture parent ID")
				}
				return v, nil
			}).(pulumi.IntOutput),
		})
		if err != nil {
			return err
		}
		ctx.Export("db", db.DbId)
		return nil
	})
}
