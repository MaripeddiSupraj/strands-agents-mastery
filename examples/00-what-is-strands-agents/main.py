from strands import Agent, tool


@tool
def get_service_status(service: str) -> str:
    """Return demo health for an approved service."""
    statuses = {"payments-api": "degraded", "orders-api": "healthy"}
    return statuses.get(service.strip().lower(), "unknown service")


agent = Agent(tools=[get_service_status])
result = agent("What is the status of payments-api?")
print(result)
