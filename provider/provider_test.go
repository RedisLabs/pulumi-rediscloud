package rediscloud_test

import (
	"os"
	"strings"
	"testing"

	rediscloud "github.com/RedisLabs/pulumi-rediscloud/provider"
)

func TestPublishedTokensStay(t *testing.T) {
	prov := rediscloud.Provider()

	resources := map[string]string{
		"rediscloud_cloud_account":                       "rediscloud:index/cloudAccount:CloudAccount",
		"rediscloud_subscription":                        "rediscloud:index/subscription:Subscription",
		"rediscloud_subscription_database":               "rediscloud:index/subscriptionDatabase:SubscriptionDatabase",
		"rediscloud_subscription_peering":                "rediscloud:index/subscriptionPeering:SubscriptionPeering",
		"rediscloud_active_active_subscription":          "rediscloud:index/activeActiveSubscription:ActiveActiveSubscription",
		"rediscloud_active_active_subscription_database": "rediscloud:index/activeActiveSubscriptionDatabase:ActiveActiveSubscriptionDatabase",
		"rediscloud_active_active_subscription_peering":  "rediscloud:index/activeActiveSubscriptionPeering:ActiveActiveSubscriptionPeering",
		"rediscloud_active_active_subscription_regions":  "rediscloud:index/activeActiveSubscriptionRegions:ActiveActiveSubscriptionRegions",
		"rediscloud_acl_user":                            "rediscloud:index/aclUser:AclUser",
		"rediscloud_acl_role":                            "rediscloud:index/aclRole:AclRole",
		"rediscloud_acl_rule":                            "rediscloud:index/aclRule:AclRule",
	}
	for tfName, want := range resources {
		info := prov.Resources[tfName]
		if info == nil || info.Tok.String() != want {
			got := ""
			if info != nil {
				got = info.Tok.String()
			}
			t.Errorf("resource %s token = %q, want %q", tfName, got, want)
		}
	}

	dataSources := map[string]string{
		"rediscloud_cloud_account":         "rediscloud:index/getCloudAccount:getCloudAccount",
		"rediscloud_data_persistence":      "rediscloud:index/getDataPersistence:getDataPersistence",
		"rediscloud_database":              "rediscloud:index/getDatabase:getDatabase",
		"rediscloud_database_modules":      "rediscloud:index/getDatabaseModules:getDatabaseModules",
		"rediscloud_payment_method":        "rediscloud:index/getPaymentMethod:getPaymentMethod",
		"rediscloud_regions":               "rediscloud:index/getRegions:getRegions",
		"rediscloud_subscription":          "rediscloud:index/getSubscription:getSubscription",
		"rediscloud_subscription_peerings": "rediscloud:index/getSubscriptionPeerings:getSubscriptionPeerings",
		"rediscloud_acl_user":              "rediscloud:index/getAclUser:getAclUser",
		"rediscloud_acl_role":              "rediscloud:index/getAclRole:getAclRole",
		"rediscloud_acl_rule":              "rediscloud:index/getAclRule:getAclRule",
	}
	for tfName, want := range dataSources {
		info := prov.DataSources[tfName]
		if info == nil || info.Tok.String() != want {
			got := ""
			if info != nil {
				got = info.Tok.String()
			}
			t.Errorf("data source %s token = %q, want %q", tfName, got, want)
		}
	}

	database := prov.Resources["rediscloud_subscription_database"]
	field := database.Fields["subscription_id"]
	if field == nil || field.Name != "subscriptionId" || field.Type != "string" {
		t.Errorf("subscription database subscription_id override = %#v", field)
	}
}

func TestLoaderIsMux(t *testing.T) {
	src := string(mustRead(t, "resources.go"))
	if strings.Contains(src, "p := shimv2.NewProvider") || strings.Contains(src, "P: shimv2.NewProvider") {
		t.Fatal("loader is shimv2.NewProvider")
	}
	if !strings.Contains(src, "MuxShimWithDisjointgPF") {
		t.Fatal("loader must be MuxShimWithDisjointgPF")
	}
	if !strings.Contains(src, "NewSdkProvider") || !strings.Contains(src, "NewFrameworkProvider") {
		t.Fatal("user agent version must go through the v2.19.3 constructors")
	}

	tfgen := string(mustRead(t, "cmd/pulumi-tfgen-rediscloud/main.go"))
	if !strings.Contains(tfgen, "MainWithMuxer") {
		t.Fatal("tfgen must use MainWithMuxer")
	}
	serve := string(mustRead(t, "cmd/pulumi-resource-rediscloud/main.go"))
	if !strings.Contains(serve, "MainWithMuxer") {
		t.Fatal("provider binary must use MainWithMuxer")
	}
}

func mustRead(t *testing.T, path string) []byte {
	t.Helper()
	contents, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return contents
}
