// Code generated by the Pulumi Terraform Bridge (tfgen) Tool DO NOT EDIT.
// *** WARNING: Do not edit by hand unless you're certain you know what you are doing! ***

package rediscloud

import (
	"context"
	"reflect"

	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

// The Cloud Account data source allows access to the ID of a Cloud Account configuration.  This ID can be
// used when creating Subscription resources.
//
// ## Example Usage
//
// The following example excludes the Redis Labs internal cloud account and returns only AWS related accounts.
// This example assumes there is only a single AWS cloud account defined.
//
// ```go
// package main
//
// import (
//
//	"github.com/RedisLabs/pulumi-rediscloud/sdk/go/rediscloud"
//	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
//
// )
//
//	func main() {
//		pulumi.Run(func(ctx *pulumi.Context) error {
//			_, err := rediscloud.LookupCloudAccount(ctx, &rediscloud.LookupCloudAccountArgs{
//				ExcludeInternalAccount: pulumi.BoolRef(true),
//				ProviderType:           pulumi.StringRef("AWS"),
//			}, nil)
//			if err != nil {
//				return err
//			}
//			return nil
//		})
//	}
//
// ```
//
// If there is more than one AWS cloud account then the name attribute can be used to further filter the ID returned.
// This example looks for a cloud account named `test` and returns the cloud account ID and access key ID.
//
// ```go
// package main
//
// import (
//
//	"github.com/RedisLabs/pulumi-rediscloud/sdk/go/rediscloud"
//	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
//
// )
//
//	func main() {
//		pulumi.Run(func(ctx *pulumi.Context) error {
//			example, err := rediscloud.LookupCloudAccount(ctx, &rediscloud.LookupCloudAccountArgs{
//				ExcludeInternalAccount: pulumi.BoolRef(true),
//				ProviderType:           pulumi.StringRef("AWS"),
//				Name:                   pulumi.StringRef("test"),
//			}, nil)
//			if err != nil {
//				return err
//			}
//			ctx.Export("cloudAccountId", example.Id)
//			ctx.Export("cloudAccountAccessKeyId", example.AccessKeyId)
//			return nil
//		})
//	}
//
// ```
func LookupCloudAccount(ctx *pulumi.Context, args *LookupCloudAccountArgs, opts ...pulumi.InvokeOption) (*LookupCloudAccountResult, error) {
	opts = pkgInvokeDefaultOpts(opts)
	var rv LookupCloudAccountResult
	err := ctx.Invoke("rediscloud:index/getCloudAccount:getCloudAccount", args, &rv, opts...)
	if err != nil {
		return nil, err
	}
	return &rv, nil
}

// A collection of arguments for invoking getCloudAccount.
type LookupCloudAccountArgs struct {
	// Whether to exclude the Redis Labs internal cloud account.
	ExcludeInternalAccount *bool `pulumi:"excludeInternalAccount"`
	// A meaningful name to identify the cloud account
	Name *string `pulumi:"name"`
	// The cloud provider of the cloud account, (either `AWS` or `GCP`)
	ProviderType *string `pulumi:"providerType"`
}

// A collection of values returned by getCloudAccount.
type LookupCloudAccountResult struct {
	// The access key ID associated with the cloud account
	AccessKeyId            string `pulumi:"accessKeyId"`
	ExcludeInternalAccount *bool  `pulumi:"excludeInternalAccount"`
	// The provider-assigned unique ID for this managed resource.
	Id           string `pulumi:"id"`
	Name         string `pulumi:"name"`
	ProviderType string `pulumi:"providerType"`
}

func LookupCloudAccountOutput(ctx *pulumi.Context, args LookupCloudAccountOutputArgs, opts ...pulumi.InvokeOption) LookupCloudAccountResultOutput {
	return pulumi.ToOutputWithContext(context.Background(), args).
		ApplyT(func(v interface{}) (LookupCloudAccountResult, error) {
			args := v.(LookupCloudAccountArgs)
			r, err := LookupCloudAccount(ctx, &args, opts...)
			var s LookupCloudAccountResult
			if r != nil {
				s = *r
			}
			return s, err
		}).(LookupCloudAccountResultOutput)
}

// A collection of arguments for invoking getCloudAccount.
type LookupCloudAccountOutputArgs struct {
	// Whether to exclude the Redis Labs internal cloud account.
	ExcludeInternalAccount pulumi.BoolPtrInput `pulumi:"excludeInternalAccount"`
	// A meaningful name to identify the cloud account
	Name pulumi.StringPtrInput `pulumi:"name"`
	// The cloud provider of the cloud account, (either `AWS` or `GCP`)
	ProviderType pulumi.StringPtrInput `pulumi:"providerType"`
}

func (LookupCloudAccountOutputArgs) ElementType() reflect.Type {
	return reflect.TypeOf((*LookupCloudAccountArgs)(nil)).Elem()
}

// A collection of values returned by getCloudAccount.
type LookupCloudAccountResultOutput struct{ *pulumi.OutputState }

func (LookupCloudAccountResultOutput) ElementType() reflect.Type {
	return reflect.TypeOf((*LookupCloudAccountResult)(nil)).Elem()
}

func (o LookupCloudAccountResultOutput) ToLookupCloudAccountResultOutput() LookupCloudAccountResultOutput {
	return o
}

func (o LookupCloudAccountResultOutput) ToLookupCloudAccountResultOutputWithContext(ctx context.Context) LookupCloudAccountResultOutput {
	return o
}

// The access key ID associated with the cloud account
func (o LookupCloudAccountResultOutput) AccessKeyId() pulumi.StringOutput {
	return o.ApplyT(func(v LookupCloudAccountResult) string { return v.AccessKeyId }).(pulumi.StringOutput)
}

func (o LookupCloudAccountResultOutput) ExcludeInternalAccount() pulumi.BoolPtrOutput {
	return o.ApplyT(func(v LookupCloudAccountResult) *bool { return v.ExcludeInternalAccount }).(pulumi.BoolPtrOutput)
}

// The provider-assigned unique ID for this managed resource.
func (o LookupCloudAccountResultOutput) Id() pulumi.StringOutput {
	return o.ApplyT(func(v LookupCloudAccountResult) string { return v.Id }).(pulumi.StringOutput)
}

func (o LookupCloudAccountResultOutput) Name() pulumi.StringOutput {
	return o.ApplyT(func(v LookupCloudAccountResult) string { return v.Name }).(pulumi.StringOutput)
}

func (o LookupCloudAccountResultOutput) ProviderType() pulumi.StringOutput {
	return o.ApplyT(func(v LookupCloudAccountResult) string { return v.ProviderType }).(pulumi.StringOutput)
}

func init() {
	pulumi.RegisterOutputType(LookupCloudAccountResultOutput{})
}
