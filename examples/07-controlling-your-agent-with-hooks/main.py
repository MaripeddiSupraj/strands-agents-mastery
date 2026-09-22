from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent


@tool
def restart_production_service(service: str) -> str:
    """Illustrative dangerous tool. It must be blocked by policy."""
    return "SHOULD NEVER RUN"


def block_production_restart(event: BeforeToolCallEvent) -> None:
    if event.tool_use["name"] == "restart_production_service":
        event.cancel_tool = "Production restart is not permitted by this runtime."


agent = Agent(tools=[restart_production_service])
agent.add_hook(block_production_restart)

result = agent("payments-api is degraded. Restart production now.")
print(result)
