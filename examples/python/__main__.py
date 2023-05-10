import pulumi
import pulumi_rediscloud

config = pulumi.Config()

rediscloud_provider = pulumi_rediscloud.Provider("rediscloud",
    api_key=config.require_secret("apiKey"),
    secret_key=config.require_secret("secretKey"),
)

card = pulumi_rediscloud.get_payment_method(
    card_type="Visa",
    last_four_numbers="3209",
    opts=pulumi.InvokeOptions(provider=rediscloud_provider),
)
