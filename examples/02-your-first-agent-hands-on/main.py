from strands import Agent, tool


@tool
def get_service_status(service: str) -> str:
    """Return demo health status for an approved service name."""
    statuses = {
        "payments-api": "degraded",
        "orders-api": "healthy",
    }
    normalized = service.strip().lower()
    if normalized not in statuses:
        return "unknown service"
    return statuses[normalized]


agent = Agent(tools=[get_service_status])
result = agent(
    "Check payments-api. If it is degraded, explain what you know "
    "without inventing a root cause."
)

print(result)
print("Tokens:", result.metrics.accumulated_usage.get("totalTokens"))
print("Tools used:", list(result.metrics.tool_metrics.keys()))
