from strands import Agent, tool
from strands.telemetry import StrandsTelemetry


StrandsTelemetry().setup_console_exporter()


@tool
def get_service_status(service: str) -> str:
    """Return demo health for an approved service."""
    return {"payments-api": "degraded"}.get(service.strip().lower(), "unknown")


agent = Agent(tools=[get_service_status])

result = agent(
    "Check payments-api. If it is degraded, tell me the next diagnostic "
    "step without inventing a root cause.",
    limits={
        "turns": 5,
        "output_tokens": 1200,
        "total_tokens": 6000,
    },
)

print("\nStop reason:", result.stop_reason)
print("Metrics:", result.metrics.get_summary())
