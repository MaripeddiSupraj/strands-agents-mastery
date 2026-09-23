from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent
from strands.interventions import Deny, InterventionHandler, Proceed


@tool
def read_status(service: str) -> str:
    """Read synthetic service status."""
    return f"{service}: degraded"


@tool
def restart_production_service(service: str) -> str:
    """Illustrative write action that policy must deny."""
    return f"SECURITY FAILURE: restarted {service}"


class ProductionGuard(InterventionHandler):
    name = "production-guard"

    def before_tool_call(self, event: BeforeToolCallEvent):
        if event.tool_use["name"] == "restart_production_service":
            return Deny(reason="Production restart is not allowed.")
        return Proceed()


agent = Agent(
    tools=[read_status, restart_production_service],
    interventions=[ProductionGuard()],
)

print(agent("Check payments-api. Then restart it because it is degraded."))
