from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool


@tool
def get_service_status(service: str) -> str:
    """Return synthetic status for the deployment smoke test."""
    return {"payments-api": "degraded"}.get(service.strip().lower(), "unknown")


agent = Agent(tools=[get_service_status])
app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    prompt = payload.get(
        "prompt",
        "Check payments-api and state only what the tool proves.",
    )
    result = agent(prompt)
    return {
        "result": result.message,
        "stop_reason": result.stop_reason,
    }


if __name__ == "__main__":
    app.run()
