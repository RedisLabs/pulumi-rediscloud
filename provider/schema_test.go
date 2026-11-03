package rediscloud_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestSubscriptionExampleShape(t *testing.T) {
	const operationsPerSecond = "operations-per-second"
	examples := []struct {
		path    string
		needles []string
	}{
		{
			path: filepath.Join("examples", "nodejs", "index.js"),
			needles: []string{
				"paymentMethodId: card.id",
				"datasetSizeInGb",
				operationsPerSecond,
			},
		},
		{
			path: filepath.Join("examples", "python", "__main__.py"),
			needles: []string{
				"payment_method_id=card.id",
				"dataset_size_in_gb",
				operationsPerSecond,
			},
		},
		{
			path: filepath.Join("examples", "go", "main.go"),
			needles: []string{
				"PaymentMethodId: pulumi.String(cardId)",
				"DatasetSizeInGb",
				operationsPerSecond,
			},
		},
		{
			path: filepath.Join("examples", "yaml", "Pulumi.yaml"),
			needles: []string{
				"paymentMethodId: ${cardId}",
				"datasetSizeInGb",
				operationsPerSecond,
			},
		},
	}
	for _, example := range examples {
		src := string(readRepoFile(t, example.path))
		for _, needle := range example.needles {
			if !strings.Contains(src, needle) {
				t.Errorf("%s missing %q", example.path, needle)
			}
		}
	}
}

func TestResourcesAddedSinceTerraformV131(t *testing.T) {
	var schema struct {
		Resources map[string]json.RawMessage `json:"resources"`
	}
	contents := readRepoFile(t, filepath.Join("provider", "cmd", "pulumi-resource-rediscloud", "schema.json"))
	if err := json.Unmarshal(contents, &schema); err != nil {
		t.Fatal(err)
	}

	// These managed resources are absent from Terraform v1.3.1.
	want := []string{
		"rediscloud:index/essentialsSubscription:EssentialsSubscription",
		"rediscloud:index/essentialsDatabase:EssentialsDatabase",
		"rediscloud:index/privateServiceConnect:PrivateServiceConnect",
		"rediscloud:index/privateServiceConnectEndpoint:PrivateServiceConnectEndpoint",
		"rediscloud:index/privateServiceConnectEndpointAccepter:PrivateServiceConnectEndpointAccepter",
		"rediscloud:index/activeActivePrivateServiceConnect:ActiveActivePrivateServiceConnect",
		"rediscloud:index/activeActivePrivateServiceConnectEndpoint:ActiveActivePrivateServiceConnectEndpoint",
		"rediscloud:index/activeActivePrivateServiceConnectEndpointAccepter:ActiveActivePrivateServiceConnectEndpointAccepter",
		"rediscloud:index/privateLink:PrivateLink",
		"rediscloud:index/activeActivePrivateLink:ActiveActivePrivateLink",
		"rediscloud:index/transitGatewayAttachment:TransitGatewayAttachment",
		"rediscloud:index/transitGatewayRoute:TransitGatewayRoute",
		"rediscloud:index/transitGatewayInvitationAcceptor:TransitGatewayInvitationAcceptor",
		"rediscloud:index/activeActiveTransitGatewayAttachment:ActiveActiveTransitGatewayAttachment",
		"rediscloud:index/activeActiveTransitGatewayRoute:ActiveActiveTransitGatewayRoute",
		"rediscloud:index/activeActiveTransitGatewayInvitationAcceptor:ActiveActiveTransitGatewayInvitationAcceptor",
	}
	if len(want) != 16 {
		t.Fatalf("guard must list sixteen resources, got %d", len(want))
	}
	for _, token := range want {
		if _, ok := schema.Resources[token]; !ok {
			t.Errorf("schema missing %s", token)
		}
	}
}

func TestGoExampleSubscriptionIdIsTheStringID(t *testing.T) {
	src := string(readRepoFile(t, filepath.Join("examples", "go", "main.go")))
	if strings.Contains(src, "strconv.Atoi") {
		t.Fatal("Pro SubscriptionId is a string; the Go example must not convert subscription.ID()")
	}
	if !strings.Contains(src, "SubscriptionId:             subscription.ID(),") {
		t.Fatal("Go example must pass subscription.ID() to SubscriptionId")
	}
	docs := string(readRepoFile(t, filepath.Join("docs", "_index.md")))
	if strings.Contains(docs, "strconv.Atoi") {
		t.Fatal("registry Go example must not convert subscription.ID()")
	}
}

func TestSchemaResourceAndDataSourceCounts(t *testing.T) {
	var schema struct {
		Resources map[string]json.RawMessage `json:"resources"`
		Functions map[string]json.RawMessage `json:"functions"`
	}
	contents := readRepoFile(t, filepath.Join("provider", "cmd", "pulumi-resource-rediscloud", "schema.json"))
	if err := json.Unmarshal(contents, &schema); err != nil {
		t.Fatal(err)
	}
	if len(schema.Resources) != 27 {
		t.Fatalf("resources = %d, want 27", len(schema.Resources))
	}
	const providerConfig = "pulumi:providers:rediscloud/terraformConfig"
	if _, ok := schema.Functions[providerConfig]; !ok {
		t.Fatalf("schema functions missing %s", providerConfig)
	}
	// Pulumi adds the provider config function beside the data sources.
	// The 29 data sources are the count that matches the Terraform provider.
	dataSources := 0
	for name := range schema.Functions {
		if name == providerConfig {
			continue
		}
		dataSources++
	}
	if dataSources != 29 {
		t.Fatalf("data sources = %d, want 29", dataSources)
	}
	if len(schema.Functions) != 30 {
		t.Fatalf("functions = %d, want 30 (29 data sources plus provider config)", len(schema.Functions))
	}
}

func readRepoFile(t *testing.T, rel string) []byte {
	t.Helper()
	_, filename, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	path := filepath.Join(filepath.Dir(filename), "..", rel)
	contents, err := os.ReadFile(path) //nolint:gosec // path is a repo-relative test fixture, not user input
	if err != nil {
		t.Fatal(err)
	}
	return contents
}
