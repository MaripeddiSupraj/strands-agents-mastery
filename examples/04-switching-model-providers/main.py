import os

from strands import Agent, tool


@tool
def get_service_status(service: str) -> str:
    """Return demo health for an approved service."""
    return {"payments-api": "degraded"}.get(service.strip().lower(), "unknown")


provider = os.getenv("MODEL_PROVIDER", "bedrock").lower()

if provider == "bedrock":
    agent = Agent(tools=[get_service_status])
elif provider == "openai":
    from strands.models.openai import OpenAIModel

    model = OpenAIModel(
        client_args={"api_key": os.environ["OPENAI_API_KEY"]},
        model_id=os.environ["OPENAI_MODEL_ID"],
    )
    agent = Agent(model=model, tools=[get_service_status])
elif provider == "anthropic":
    from strands.models.anthropic import AnthropicModel

    model = AnthropicModel(
        client_args={"api_key": os.environ["ANTHROPIC_API_KEY"]},
        model_id=os.environ["ANTHROPIC_MODEL_ID"],
    )
    agent = Agent(model=model, tools=[get_service_status])
else:
    raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}")

result = agent(
    "Check payments-api. If degraded, recommend the next diagnostic step "
    "without inventing a root cause."
)

print(result)
print("Provider:", provider)
print("Stop reason:", result.stop_reason)
print("Metrics:", result.metrics.get_summary())
