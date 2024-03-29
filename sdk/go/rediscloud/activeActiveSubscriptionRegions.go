// Code generated by the Pulumi Terraform Bridge (tfgen) Tool DO NOT EDIT.
// *** WARNING: Do not edit by hand unless you're certain you know what you are doing! ***

package rediscloud

import (
	"context"
	"reflect"

	"errors"
	"github.com/RedisLabs/pulumi-rediscloud/sdk/go/rediscloud/internal"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumix"
)

// Manages regions within your Redis Enterprise Cloud Active-Active subscription.
// This resource is responsible for creating and managing regions within that subscription.
// This allows Redis Enterprise Cloud to efficiently provision your cluster within each defined region in a separate block.
//
// ## Example Usage
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
//			_, err := rediscloud.NewActiveActiveSubscriptionRegions(ctx, "regions-resource", &rediscloud.ActiveActiveSubscriptionRegionsArgs{
//				SubscriptionId: pulumi.Any(rediscloud_active_active_subscription.SubscriptionResource.Id),
//				DeleteRegions:  pulumi.Bool(false),
//				Regions: rediscloud.ActiveActiveSubscriptionRegionsRegionArray{
//					&rediscloud.ActiveActiveSubscriptionRegionsRegionArgs{
//						Region:                   pulumi.String("us-east-1"),
//						NetworkingDeploymentCidr: pulumi.String("192.168.0.0/24"),
//						Databases: rediscloud.ActiveActiveSubscriptionRegionsRegionDatabaseArray{
//							&rediscloud.ActiveActiveSubscriptionRegionsRegionDatabaseArgs{
//								DatabaseId:                    pulumi.Any(rediscloud_active_active_subscription_database.DatabaseResource.Db_id),
//								DatabaseName:                  pulumi.Any(rediscloud_active_active_subscription_database.DatabaseResource.Name),
//								LocalWriteOperationsPerSecond: pulumi.Int(1000),
//								LocalReadOperationsPerSecond:  pulumi.Int(1000),
//							},
//						},
//					},
//					&rediscloud.ActiveActiveSubscriptionRegionsRegionArgs{
//						Region:                   pulumi.String("us-east-2"),
//						NetworkingDeploymentCidr: pulumi.String("10.0.1.0/24"),
//						Databases: rediscloud.ActiveActiveSubscriptionRegionsRegionDatabaseArray{
//							&rediscloud.ActiveActiveSubscriptionRegionsRegionDatabaseArgs{
//								DatabaseId:                    pulumi.Any(rediscloud_active_active_subscription_database.DatabaseResource.Db_id),
//								DatabaseName:                  pulumi.Any(rediscloud_active_active_subscription_database.DatabaseResource.Name),
//								LocalWriteOperationsPerSecond: pulumi.Int(2000),
//								LocalReadOperationsPerSecond:  pulumi.Int(4000),
//							},
//						},
//					},
//				},
//			})
//			if err != nil {
//				return err
//			}
//			return nil
//		})
//	}
//
// ```
//
// ## Import
//
// `rediscloud_active_active_regions` can be imported using the ID of the subscription, e.g.
//
// ```sh
//
//	$ pulumi import rediscloud:index/activeActiveSubscriptionRegions:ActiveActiveSubscriptionRegions regions-resource 12345678
//
// ```
type ActiveActiveSubscriptionRegions struct {
	pulumi.CustomResourceState

	// Flag required to be set when one or more regions is to be deleted, if the flag is not set an error will be thrown
	DeleteRegions pulumi.BoolPtrOutput `pulumi:"deleteRegions"`
	// Cloud networking details, per region, documented below
	Regions ActiveActiveSubscriptionRegionsRegionArrayOutput `pulumi:"regions"`
	// ID of the subscription that the regions belong to. **Modifying this attribute will force creation of a new resource.**
	SubscriptionId pulumi.StringOutput `pulumi:"subscriptionId"`
}

// NewActiveActiveSubscriptionRegions registers a new resource with the given unique name, arguments, and options.
func NewActiveActiveSubscriptionRegions(ctx *pulumi.Context,
	name string, args *ActiveActiveSubscriptionRegionsArgs, opts ...pulumi.ResourceOption) (*ActiveActiveSubscriptionRegions, error) {
	if args == nil {
		return nil, errors.New("missing one or more required arguments")
	}

	if args.Regions == nil {
		return nil, errors.New("invalid value for required argument 'Regions'")
	}
	if args.SubscriptionId == nil {
		return nil, errors.New("invalid value for required argument 'SubscriptionId'")
	}
	opts = internal.PkgResourceDefaultOpts(opts)
	var resource ActiveActiveSubscriptionRegions
	err := ctx.RegisterResource("rediscloud:index/activeActiveSubscriptionRegions:ActiveActiveSubscriptionRegions", name, args, &resource, opts...)
	if err != nil {
		return nil, err
	}
	return &resource, nil
}

// GetActiveActiveSubscriptionRegions gets an existing ActiveActiveSubscriptionRegions resource's state with the given name, ID, and optional
// state properties that are used to uniquely qualify the lookup (nil if not required).
func GetActiveActiveSubscriptionRegions(ctx *pulumi.Context,
	name string, id pulumi.IDInput, state *ActiveActiveSubscriptionRegionsState, opts ...pulumi.ResourceOption) (*ActiveActiveSubscriptionRegions, error) {
	var resource ActiveActiveSubscriptionRegions
	err := ctx.ReadResource("rediscloud:index/activeActiveSubscriptionRegions:ActiveActiveSubscriptionRegions", name, id, state, &resource, opts...)
	if err != nil {
		return nil, err
	}
	return &resource, nil
}

// Input properties used for looking up and filtering ActiveActiveSubscriptionRegions resources.
type activeActiveSubscriptionRegionsState struct {
	// Flag required to be set when one or more regions is to be deleted, if the flag is not set an error will be thrown
	DeleteRegions *bool `pulumi:"deleteRegions"`
	// Cloud networking details, per region, documented below
	Regions []ActiveActiveSubscriptionRegionsRegion `pulumi:"regions"`
	// ID of the subscription that the regions belong to. **Modifying this attribute will force creation of a new resource.**
	SubscriptionId *string `pulumi:"subscriptionId"`
}

type ActiveActiveSubscriptionRegionsState struct {
	// Flag required to be set when one or more regions is to be deleted, if the flag is not set an error will be thrown
	DeleteRegions pulumi.BoolPtrInput
	// Cloud networking details, per region, documented below
	Regions ActiveActiveSubscriptionRegionsRegionArrayInput
	// ID of the subscription that the regions belong to. **Modifying this attribute will force creation of a new resource.**
	SubscriptionId pulumi.StringPtrInput
}

func (ActiveActiveSubscriptionRegionsState) ElementType() reflect.Type {
	return reflect.TypeOf((*activeActiveSubscriptionRegionsState)(nil)).Elem()
}

type activeActiveSubscriptionRegionsArgs struct {
	// Flag required to be set when one or more regions is to be deleted, if the flag is not set an error will be thrown
	DeleteRegions *bool `pulumi:"deleteRegions"`
	// Cloud networking details, per region, documented below
	Regions []ActiveActiveSubscriptionRegionsRegion `pulumi:"regions"`
	// ID of the subscription that the regions belong to. **Modifying this attribute will force creation of a new resource.**
	SubscriptionId string `pulumi:"subscriptionId"`
}

// The set of arguments for constructing a ActiveActiveSubscriptionRegions resource.
type ActiveActiveSubscriptionRegionsArgs struct {
	// Flag required to be set when one or more regions is to be deleted, if the flag is not set an error will be thrown
	DeleteRegions pulumi.BoolPtrInput
	// Cloud networking details, per region, documented below
	Regions ActiveActiveSubscriptionRegionsRegionArrayInput
	// ID of the subscription that the regions belong to. **Modifying this attribute will force creation of a new resource.**
	SubscriptionId pulumi.StringInput
}

func (ActiveActiveSubscriptionRegionsArgs) ElementType() reflect.Type {
	return reflect.TypeOf((*activeActiveSubscriptionRegionsArgs)(nil)).Elem()
}

type ActiveActiveSubscriptionRegionsInput interface {
	pulumi.Input

	ToActiveActiveSubscriptionRegionsOutput() ActiveActiveSubscriptionRegionsOutput
	ToActiveActiveSubscriptionRegionsOutputWithContext(ctx context.Context) ActiveActiveSubscriptionRegionsOutput
}

func (*ActiveActiveSubscriptionRegions) ElementType() reflect.Type {
	return reflect.TypeOf((**ActiveActiveSubscriptionRegions)(nil)).Elem()
}

func (i *ActiveActiveSubscriptionRegions) ToActiveActiveSubscriptionRegionsOutput() ActiveActiveSubscriptionRegionsOutput {
	return i.ToActiveActiveSubscriptionRegionsOutputWithContext(context.Background())
}

func (i *ActiveActiveSubscriptionRegions) ToActiveActiveSubscriptionRegionsOutputWithContext(ctx context.Context) ActiveActiveSubscriptionRegionsOutput {
	return pulumi.ToOutputWithContext(ctx, i).(ActiveActiveSubscriptionRegionsOutput)
}

func (i *ActiveActiveSubscriptionRegions) ToOutput(ctx context.Context) pulumix.Output[*ActiveActiveSubscriptionRegions] {
	return pulumix.Output[*ActiveActiveSubscriptionRegions]{
		OutputState: i.ToActiveActiveSubscriptionRegionsOutputWithContext(ctx).OutputState,
	}
}

// ActiveActiveSubscriptionRegionsArrayInput is an input type that accepts ActiveActiveSubscriptionRegionsArray and ActiveActiveSubscriptionRegionsArrayOutput values.
// You can construct a concrete instance of `ActiveActiveSubscriptionRegionsArrayInput` via:
//
//	ActiveActiveSubscriptionRegionsArray{ ActiveActiveSubscriptionRegionsArgs{...} }
type ActiveActiveSubscriptionRegionsArrayInput interface {
	pulumi.Input

	ToActiveActiveSubscriptionRegionsArrayOutput() ActiveActiveSubscriptionRegionsArrayOutput
	ToActiveActiveSubscriptionRegionsArrayOutputWithContext(context.Context) ActiveActiveSubscriptionRegionsArrayOutput
}

type ActiveActiveSubscriptionRegionsArray []ActiveActiveSubscriptionRegionsInput

func (ActiveActiveSubscriptionRegionsArray) ElementType() reflect.Type {
	return reflect.TypeOf((*[]*ActiveActiveSubscriptionRegions)(nil)).Elem()
}

func (i ActiveActiveSubscriptionRegionsArray) ToActiveActiveSubscriptionRegionsArrayOutput() ActiveActiveSubscriptionRegionsArrayOutput {
	return i.ToActiveActiveSubscriptionRegionsArrayOutputWithContext(context.Background())
}

func (i ActiveActiveSubscriptionRegionsArray) ToActiveActiveSubscriptionRegionsArrayOutputWithContext(ctx context.Context) ActiveActiveSubscriptionRegionsArrayOutput {
	return pulumi.ToOutputWithContext(ctx, i).(ActiveActiveSubscriptionRegionsArrayOutput)
}

func (i ActiveActiveSubscriptionRegionsArray) ToOutput(ctx context.Context) pulumix.Output[[]*ActiveActiveSubscriptionRegions] {
	return pulumix.Output[[]*ActiveActiveSubscriptionRegions]{
		OutputState: i.ToActiveActiveSubscriptionRegionsArrayOutputWithContext(ctx).OutputState,
	}
}

// ActiveActiveSubscriptionRegionsMapInput is an input type that accepts ActiveActiveSubscriptionRegionsMap and ActiveActiveSubscriptionRegionsMapOutput values.
// You can construct a concrete instance of `ActiveActiveSubscriptionRegionsMapInput` via:
//
//	ActiveActiveSubscriptionRegionsMap{ "key": ActiveActiveSubscriptionRegionsArgs{...} }
type ActiveActiveSubscriptionRegionsMapInput interface {
	pulumi.Input

	ToActiveActiveSubscriptionRegionsMapOutput() ActiveActiveSubscriptionRegionsMapOutput
	ToActiveActiveSubscriptionRegionsMapOutputWithContext(context.Context) ActiveActiveSubscriptionRegionsMapOutput
}

type ActiveActiveSubscriptionRegionsMap map[string]ActiveActiveSubscriptionRegionsInput

func (ActiveActiveSubscriptionRegionsMap) ElementType() reflect.Type {
	return reflect.TypeOf((*map[string]*ActiveActiveSubscriptionRegions)(nil)).Elem()
}

func (i ActiveActiveSubscriptionRegionsMap) ToActiveActiveSubscriptionRegionsMapOutput() ActiveActiveSubscriptionRegionsMapOutput {
	return i.ToActiveActiveSubscriptionRegionsMapOutputWithContext(context.Background())
}

func (i ActiveActiveSubscriptionRegionsMap) ToActiveActiveSubscriptionRegionsMapOutputWithContext(ctx context.Context) ActiveActiveSubscriptionRegionsMapOutput {
	return pulumi.ToOutputWithContext(ctx, i).(ActiveActiveSubscriptionRegionsMapOutput)
}

func (i ActiveActiveSubscriptionRegionsMap) ToOutput(ctx context.Context) pulumix.Output[map[string]*ActiveActiveSubscriptionRegions] {
	return pulumix.Output[map[string]*ActiveActiveSubscriptionRegions]{
		OutputState: i.ToActiveActiveSubscriptionRegionsMapOutputWithContext(ctx).OutputState,
	}
}

type ActiveActiveSubscriptionRegionsOutput struct{ *pulumi.OutputState }

func (ActiveActiveSubscriptionRegionsOutput) ElementType() reflect.Type {
	return reflect.TypeOf((**ActiveActiveSubscriptionRegions)(nil)).Elem()
}

func (o ActiveActiveSubscriptionRegionsOutput) ToActiveActiveSubscriptionRegionsOutput() ActiveActiveSubscriptionRegionsOutput {
	return o
}

func (o ActiveActiveSubscriptionRegionsOutput) ToActiveActiveSubscriptionRegionsOutputWithContext(ctx context.Context) ActiveActiveSubscriptionRegionsOutput {
	return o
}

func (o ActiveActiveSubscriptionRegionsOutput) ToOutput(ctx context.Context) pulumix.Output[*ActiveActiveSubscriptionRegions] {
	return pulumix.Output[*ActiveActiveSubscriptionRegions]{
		OutputState: o.OutputState,
	}
}

// Flag required to be set when one or more regions is to be deleted, if the flag is not set an error will be thrown
func (o ActiveActiveSubscriptionRegionsOutput) DeleteRegions() pulumi.BoolPtrOutput {
	return o.ApplyT(func(v *ActiveActiveSubscriptionRegions) pulumi.BoolPtrOutput { return v.DeleteRegions }).(pulumi.BoolPtrOutput)
}

// Cloud networking details, per region, documented below
func (o ActiveActiveSubscriptionRegionsOutput) Regions() ActiveActiveSubscriptionRegionsRegionArrayOutput {
	return o.ApplyT(func(v *ActiveActiveSubscriptionRegions) ActiveActiveSubscriptionRegionsRegionArrayOutput {
		return v.Regions
	}).(ActiveActiveSubscriptionRegionsRegionArrayOutput)
}

// ID of the subscription that the regions belong to. **Modifying this attribute will force creation of a new resource.**
func (o ActiveActiveSubscriptionRegionsOutput) SubscriptionId() pulumi.StringOutput {
	return o.ApplyT(func(v *ActiveActiveSubscriptionRegions) pulumi.StringOutput { return v.SubscriptionId }).(pulumi.StringOutput)
}

type ActiveActiveSubscriptionRegionsArrayOutput struct{ *pulumi.OutputState }

func (ActiveActiveSubscriptionRegionsArrayOutput) ElementType() reflect.Type {
	return reflect.TypeOf((*[]*ActiveActiveSubscriptionRegions)(nil)).Elem()
}

func (o ActiveActiveSubscriptionRegionsArrayOutput) ToActiveActiveSubscriptionRegionsArrayOutput() ActiveActiveSubscriptionRegionsArrayOutput {
	return o
}

func (o ActiveActiveSubscriptionRegionsArrayOutput) ToActiveActiveSubscriptionRegionsArrayOutputWithContext(ctx context.Context) ActiveActiveSubscriptionRegionsArrayOutput {
	return o
}

func (o ActiveActiveSubscriptionRegionsArrayOutput) ToOutput(ctx context.Context) pulumix.Output[[]*ActiveActiveSubscriptionRegions] {
	return pulumix.Output[[]*ActiveActiveSubscriptionRegions]{
		OutputState: o.OutputState,
	}
}

func (o ActiveActiveSubscriptionRegionsArrayOutput) Index(i pulumi.IntInput) ActiveActiveSubscriptionRegionsOutput {
	return pulumi.All(o, i).ApplyT(func(vs []interface{}) *ActiveActiveSubscriptionRegions {
		return vs[0].([]*ActiveActiveSubscriptionRegions)[vs[1].(int)]
	}).(ActiveActiveSubscriptionRegionsOutput)
}

type ActiveActiveSubscriptionRegionsMapOutput struct{ *pulumi.OutputState }

func (ActiveActiveSubscriptionRegionsMapOutput) ElementType() reflect.Type {
	return reflect.TypeOf((*map[string]*ActiveActiveSubscriptionRegions)(nil)).Elem()
}

func (o ActiveActiveSubscriptionRegionsMapOutput) ToActiveActiveSubscriptionRegionsMapOutput() ActiveActiveSubscriptionRegionsMapOutput {
	return o
}

func (o ActiveActiveSubscriptionRegionsMapOutput) ToActiveActiveSubscriptionRegionsMapOutputWithContext(ctx context.Context) ActiveActiveSubscriptionRegionsMapOutput {
	return o
}

func (o ActiveActiveSubscriptionRegionsMapOutput) ToOutput(ctx context.Context) pulumix.Output[map[string]*ActiveActiveSubscriptionRegions] {
	return pulumix.Output[map[string]*ActiveActiveSubscriptionRegions]{
		OutputState: o.OutputState,
	}
}

func (o ActiveActiveSubscriptionRegionsMapOutput) MapIndex(k pulumi.StringInput) ActiveActiveSubscriptionRegionsOutput {
	return pulumi.All(o, k).ApplyT(func(vs []interface{}) *ActiveActiveSubscriptionRegions {
		return vs[0].(map[string]*ActiveActiveSubscriptionRegions)[vs[1].(string)]
	}).(ActiveActiveSubscriptionRegionsOutput)
}

func init() {
	pulumi.RegisterInputType(reflect.TypeOf((*ActiveActiveSubscriptionRegionsInput)(nil)).Elem(), &ActiveActiveSubscriptionRegions{})
	pulumi.RegisterInputType(reflect.TypeOf((*ActiveActiveSubscriptionRegionsArrayInput)(nil)).Elem(), ActiveActiveSubscriptionRegionsArray{})
	pulumi.RegisterInputType(reflect.TypeOf((*ActiveActiveSubscriptionRegionsMapInput)(nil)).Elem(), ActiveActiveSubscriptionRegionsMap{})
	pulumi.RegisterOutputType(ActiveActiveSubscriptionRegionsOutput{})
	pulumi.RegisterOutputType(ActiveActiveSubscriptionRegionsArrayOutput{})
	pulumi.RegisterOutputType(ActiveActiveSubscriptionRegionsMapOutput{})
}
