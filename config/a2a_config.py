from a2a.types import SecurityScheme, AgentProvider, PushNotificationConfig

A2A_SECURITY = SecurityScheme(
    type="bearer",
    description="Bearer token authentication"
)

A2A_PROVIDER = AgentProvider(
    name="Shopping Assistant",
    url="https://your-domain.com"
)

A2A_PUSH_CONFIG = PushNotificationConfig(
    enabled=True,
    webhook_url="https://your-domain.com/webhook",
    authentication_info={
        "type": "bearer",
        "token": "your-webhook-token"
    }
) 