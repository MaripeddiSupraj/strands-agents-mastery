from strands import Agent, tool


@tool
def get_service_status(service: str) -> str:
    """Return demo status for an approved service."""
    return {"payments-api": "degraded"}.get(service.strip().lower(), "unknown")


agent = Agent(tools=[get_service_status], context_manager="auto")

print("Tools:", agent.tool_names)
print("Tool configs:", agent.tool_registry.get_all_tools_config())

result = agent("Check payments-api and state only what the tool proves.")

print("Stop reason:", result.stop_reason)
print("Metrics:", result.metrics.get_summary())
