// Copyright 2016-2018, Pulumi Corporation.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package rediscloud

import (
	"fmt"
	"path/filepath"

	"github.com/RedisLabs/pulumi-rediscloud/provider/pkg/version"
	rediscloud "github.com/RedisLabs/terraform-provider-rediscloud/provider"
	"github.com/pulumi/pulumi-terraform-bridge/v3/pkg/tfbridge"
	shim "github.com/pulumi/pulumi-terraform-bridge/v3/pkg/tfshim"
	shimv2 "github.com/pulumi/pulumi-terraform-bridge/v3/pkg/tfshim/sdk-v2"
	"github.com/pulumi/pulumi/sdk/v3/go/common/resource"
)

// all of the token components used below.
const (
	// This variable controls the default name of the package in the package
	// registries for nodejs and python:
	mainPkg = "rediscloud"
	// modules:
	mainMod = "index" // the rediscloud module
)

// preConfigureCallback is called before the providerConfigure function of the underlying provider.
// It should validate that the provider can be configured, and provide actionable errors in the case
// it cannot be. Configuration variables can be read from `vars` using the `stringValue` function -
// for example `stringValue(vars, "accessKey")`.
func preConfigureCallback(vars resource.PropertyMap, c shim.ResourceConfig) error {
	return nil
}

// Provider returns additional overlaid schema and metadata associated with the provider..
func Provider() tfbridge.ProviderInfo {
	// Instantiate the Terraform provider
	p := shimv2.NewProvider(rediscloud.New("pulumi")())

	// Create a Pulumi provider mapping
	prov := tfbridge.ProviderInfo{
		P:    p,
		Name: "rediscloud",
		// DisplayName is a way to be able to change the casing of the provider
		// name when being displayed on the Pulumi registry
		DisplayName: "Redis Cloud",
		// The default publisher for all packages is Pulumi.
		// Change this to your personal name (or a company name) that you
		// would like to be shown in the Pulumi Registry if this package is published
		// there.
		Publisher: "RedisLabs",
		// LogoURL is optional but useful to help identify your package in the Pulumi Registry
		// if this package is published there.
		//
		// You may host a logo on a domain you control or add an SVG logo for your package
		// in your repository and use the raw content URL for that file as your logo URL.
		LogoURL: "https://avatars.githubusercontent.com/u/1991868?s=200&v=4",
		// PluginDownloadURL is an optional URL used to download the Provider
		// for use in Pulumi programs
		// e.g https://github.com/org/pulumi-provider-name/releases/
		PluginDownloadURL: "github://api.github.com/RedisLabs/pulumi-rediscloud",
		Description:       "A Pulumi package for creating and managing rediscloud cloud resources.",
		// category/cloud tag helps with categorizing the package in the Pulumi Registry.
		// For all available categories, see `Keywords` in
		// https://www.pulumi.com/docs/guides/pulumi-packages/schema/#package.
		Keywords:   []string{"pulumi", "rediscloud", "category/cloud"},
		License:    "Apache-2.0",
		Homepage:   "https://www.pulumi.com",
		Repository: "https://github.com/RedisLabs/pulumi-rediscloud",
		// The GitHub Org for the provider - defaults to `terraform-providers`. Note that this
		// should match the TF provider module's require directive, not any replace directives.
		GitHubOrg: "RedisLabs",
		Config: map[string]*tfbridge.SchemaInfo{
			"api_key": {
				Secret: tfbridge.True(),
				Default: &tfbridge.DefaultInfo{
					EnvVars: []string{"REDISCLOUD_API_KEY"},
				},
			},
			"secret_key": {
				Secret: tfbridge.True(),
				Default: &tfbridge.DefaultInfo{
					EnvVars: []string{"REDISCLOUD_SECRET_KEY"},
				},
			},
		},
		PreConfigureCallback: preConfigureCallback,
		Resources: map[string]*tfbridge.ResourceInfo{
			"rediscloud_cloud_account": {
				Tok: tfbridge.MakeResource(mainPkg, mainMod, "CloudAccount"),
			},
			"rediscloud_subscription": {
				Tok: tfbridge.MakeResource(mainPkg, mainMod, "Subscription"),
			},
			"rediscloud_subscription_database": {
				Tok: tfbridge.MakeResource(mainPkg, mainMod, "SubscriptionDatabase"),
			},
			"rediscloud_subscription_peering": {
				Tok: tfbridge.MakeResource(mainPkg, mainMod, "SubscriptionPeering"),
			},
			"rediscloud_active_active_subscription": {
				Tok: tfbridge.MakeResource(mainPkg, mainMod, "ActiveActiveSubscription"),
			},
			"rediscloud_active_active_subscription_database": {
				Tok: tfbridge.MakeResource(mainPkg, mainMod, "ActiveActiveSubscriptionDatabase"),
			},
			"rediscloud_active_active_subscription_peering": {
				Tok: tfbridge.MakeResource(mainPkg, mainMod, "ActiveActiveSubscriptionPeering"),
			},
			"rediscloud_active_active_subscription_regions": {
				Tok: tfbridge.MakeResource(mainPkg, mainMod, "ActiveActiveSubscriptionRegions"),
			},
		},
		DataSources: map[string]*tfbridge.DataSourceInfo{
			"rediscloud_cloud_account":         {Tok: tfbridge.MakeDataSource(mainPkg, mainMod, "getCloudAccount")},
			"rediscloud_data_persistence":      {Tok: tfbridge.MakeDataSource(mainPkg, mainMod, "getDataPersistence")},
			"rediscloud_database":              {Tok: tfbridge.MakeDataSource(mainPkg, mainMod, "getDatabase")},
			"rediscloud_database_modules":      {Tok: tfbridge.MakeDataSource(mainPkg, mainMod, "getDatabaseModules")},
			"rediscloud_payment_method":        {Tok: tfbridge.MakeDataSource(mainPkg, mainMod, "getPaymentMethod")},
			"rediscloud_regions":               {Tok: tfbridge.MakeDataSource(mainPkg, mainMod, "getRegions")},
			"rediscloud_subscription":          {Tok: tfbridge.MakeDataSource(mainPkg, mainMod, "getSubscription")},
			"rediscloud_subscription_peerings": {Tok: tfbridge.MakeDataSource(mainPkg, mainMod, "getSubscriptionPeerings")},
		},
		JavaScript: &tfbridge.JavaScriptInfo{
			PackageName: "@rediscloud/pulumi-rediscloud",
			// List any npm dependencies and their versions
			Dependencies: map[string]string{
				"@pulumi/pulumi": "^3.0.0",
			},
			DevDependencies: map[string]string{
				"@types/node": "^10.0.0", // so we can access strongly typed node definitions.
				"@types/mime": "^2.0.0",
			},
			// See the documentation for tfbridge.OverlayInfo for how to lay out this
			// section, or refer to the AWS provider. Delete this section if there are
			// no overlay files.
			//Overlay: &tfbridge.OverlayInfo{},
		},
		Python: &tfbridge.PythonInfo{
			PackageName: "pulumi_rediscloud",
			// List any Python dependencies and their version ranges
			Requires: map[string]string{
				"pulumi": ">=3.0.0,<4.0.0",
			},
		},
		Golang: &tfbridge.GolangInfo{
			ImportBasePath: filepath.Join(
				fmt.Sprintf("github.com/RedisLabs/pulumi-%[1]s/sdk/", mainPkg),
				tfbridge.GetModuleMajorVersion(version.Version),
				"go",
				mainPkg,
			),
			GenerateResourceContainerTypes: true,
		},
		CSharp: &tfbridge.CSharpInfo{
			RootNamespace: "RedisLabs",
			PackageReferences: map[string]string{
				"Pulumi": "3.*",
			},
		},
		Java: &tfbridge.JavaInfo{
			BasePackage: "com.redislabs",
		},
	}

	prov.SetAutonaming(255, "-")

	return prov
}
