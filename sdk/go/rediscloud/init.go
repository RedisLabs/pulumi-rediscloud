// Code generated by the Pulumi Terraform Bridge (tfgen) Tool DO NOT EDIT.
// *** WARNING: Do not edit by hand unless you're certain you know what you are doing! ***

package rediscloud

import (
	"fmt"

	"github.com/RedisLabs/pulumi-rediscloud/sdk/go/rediscloud/internal"
	"github.com/blang/semver"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

type module struct {
	version semver.Version
}

func (m *module) Version() semver.Version {
	return m.version
}

func (m *module) Construct(ctx *pulumi.Context, name, typ, urn string) (r pulumi.Resource, err error) {
	switch typ {
	case "rediscloud:index/aclRole:AclRole":
		r = &AclRole{}
	case "rediscloud:index/aclRule:AclRule":
		r = &AclRule{}
	case "rediscloud:index/aclUser:AclUser":
		r = &AclUser{}
	case "rediscloud:index/activeActiveSubscription:ActiveActiveSubscription":
		r = &ActiveActiveSubscription{}
	case "rediscloud:index/activeActiveSubscriptionDatabase:ActiveActiveSubscriptionDatabase":
		r = &ActiveActiveSubscriptionDatabase{}
	case "rediscloud:index/activeActiveSubscriptionPeering:ActiveActiveSubscriptionPeering":
		r = &ActiveActiveSubscriptionPeering{}
	case "rediscloud:index/activeActiveSubscriptionRegions:ActiveActiveSubscriptionRegions":
		r = &ActiveActiveSubscriptionRegions{}
	case "rediscloud:index/cloudAccount:CloudAccount":
		r = &CloudAccount{}
	case "rediscloud:index/subscription:Subscription":
		r = &Subscription{}
	case "rediscloud:index/subscriptionDatabase:SubscriptionDatabase":
		r = &SubscriptionDatabase{}
	case "rediscloud:index/subscriptionPeering:SubscriptionPeering":
		r = &SubscriptionPeering{}
	default:
		return nil, fmt.Errorf("unknown resource type: %s", typ)
	}

	err = ctx.RegisterResource(typ, name, nil, r, pulumi.URN_(urn))
	return
}

type pkg struct {
	version semver.Version
}

func (p *pkg) Version() semver.Version {
	return p.version
}

func (p *pkg) ConstructProvider(ctx *pulumi.Context, name, typ, urn string) (pulumi.ProviderResource, error) {
	if typ != "pulumi:providers:rediscloud" {
		return nil, fmt.Errorf("unknown provider type: %s", typ)
	}

	r := &Provider{}
	err := ctx.RegisterResource(typ, name, nil, r, pulumi.URN_(urn))
	return r, err
}

func init() {
	version, err := internal.PkgVersion()
	if err != nil {
		version = semver.Version{Major: 1}
	}
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/aclRole",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/aclRule",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/aclUser",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/activeActiveSubscription",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/activeActiveSubscriptionDatabase",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/activeActiveSubscriptionPeering",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/activeActiveSubscriptionRegions",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/cloudAccount",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/subscription",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/subscriptionDatabase",
		&module{version},
	)
	pulumi.RegisterResourceModule(
		"rediscloud",
		"index/subscriptionPeering",
		&module{version},
	)
	pulumi.RegisterResourcePackage(
		"rediscloud",
		&pkg{version},
	)
}
