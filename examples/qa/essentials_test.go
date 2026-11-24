package main

import (
	"fmt"
	"sync"
	"testing"

	"github.com/pulumi/pulumi/sdk/v3/go/common/resource"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

type essentialsMocks struct {
	mu             sync.Mutex
	resources      []pulumi.MockResourceArgs
	subscriptionID string
}

func (m *essentialsMocks) Call(pulumi.MockCallArgs) (resource.PropertyMap, error) {
	return nil, fmt.Errorf("unexpected provider lookup")
}

func (m *essentialsMocks) NewResource(args pulumi.MockResourceArgs) (string, resource.PropertyMap, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.resources = append(m.resources, args)
	switch args.TypeToken {
	case "rediscloud:index/essentialsSubscription:EssentialsSubscription":
		return m.subscriptionID, args.Inputs, nil
	case "rediscloud:index/essentialsDatabase:EssentialsDatabase":
		args.Inputs["dbId"] = resource.NewNumberProperty(81)
		return "81", args.Inputs, nil
	default:
		return "", nil, fmt.Errorf("unexpected resource token %s", args.TypeToken)
	}
}

func TestEssentialsProgramRegistersLinkedResources(t *testing.T) {
	mocks := &essentialsMocks{subscriptionID: "42"}
	err := pulumi.RunErr(func(ctx *pulumi.Context) error {
		return createEssentials(ctx, "qa-example", 7, "3", true)
	}, pulumi.WithMocks("qa", "dev", mocks))
	if err != nil {
		t.Fatal(err)
	}
	mocks.mu.Lock()
	defer mocks.mu.Unlock()
	if len(mocks.resources) != 2 {
		t.Fatalf("expected two resources; got %d", len(mocks.resources))
	}
	sub, db := mocks.resources[0], mocks.resources[1]
	if sub.TypeToken != "rediscloud:index/essentialsSubscription:EssentialsSubscription" ||
		sub.Inputs["planId"].NumberValue() != 7 || sub.Inputs["paymentMethodId"].NumberValue() != 3 {
		t.Fatalf("unexpected subscription request: %v", sub.Inputs)
	}
	if db.TypeToken != "rediscloud:index/essentialsDatabase:EssentialsDatabase" ||
		db.Inputs["subscriptionId"].NumberValue() != 42 || db.Inputs["dataPersistence"].StringValue() != "none" || db.Inputs["replication"].BoolValue() {
		t.Fatalf("unexpected database request: %v", db.Inputs)
	}
}

func TestEssentialsInvalidInputsDoNotRegisterResources(t *testing.T) {
	for _, c := range []struct {
		name string
		plan int
		card string
	}{{"", 7, "3"}, {"x", 0, "3"}, {"x", 7, "invalid"}, {"x", 7, "0"}} {
		mocks := &essentialsMocks{subscriptionID: "42"}
		err := pulumi.RunErr(func(ctx *pulumi.Context) error { return createEssentials(ctx, c.name, c.plan, c.card, true) }, pulumi.WithMocks("qa", "dev", mocks))
		if err == nil || len(mocks.resources) != 0 {
			t.Fatalf("invalid inputs sent resources: %v, %v", err, mocks.resources)
		}
	}
}

func TestEssentialsRejectsInvalidSubscriptionID(t *testing.T) {
	mocks := &essentialsMocks{subscriptionID: "not-a-number"}
	err := pulumi.RunErr(func(ctx *pulumi.Context) error { return createEssentials(ctx, "x", 7, "3", true) }, pulumi.WithMocks("qa", "dev", mocks))
	if err == nil {
		t.Fatal("invalid subscription ID must fail")
	}
	for _, item := range mocks.resources {
		if item.TypeToken == "rediscloud:index/essentialsDatabase:EssentialsDatabase" {
			t.Fatal("database must not register for invalid parent ID")
		}
	}
}

func TestEssentialsSubscriptionOnly(t *testing.T) {
	mocks := &essentialsMocks{subscriptionID: "42"}
	err := pulumi.RunErr(func(ctx *pulumi.Context) error {
		return createEssentials(ctx, "qa-example", 7, "3", false)
	}, pulumi.WithMocks("qa", "dev", mocks))
	if err != nil {
		t.Fatal(err)
	}
	if len(mocks.resources) != 1 || mocks.resources[0].TypeToken != "rediscloud:index/essentialsSubscription:EssentialsSubscription" {
		t.Fatalf("expected only subscription, got %v", mocks.resources)
	}
}
