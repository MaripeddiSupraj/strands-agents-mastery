import time

from strands import Agent, tool
from strands.telemetry import StrandsTelemetry


StrandsTelemetry().setup_console_exporter()


@tool
def slow_status_check(service: str) -> str:
    """Synthetic slow dependency used to make tool latency visible."""
    time.sleep(2)
    return f"{service}: degraded"


agent = Agent(tools=[slow_status_check])

result = agent(
    "Check payments-api. Explain the status without inventing a root cause."
)

print(result)
print("Stop reason:", result.stop_reason)
print("Metrics:", result.metrics.get_summary())
