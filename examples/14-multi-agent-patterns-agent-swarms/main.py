from strands import Agent
from strands.multiagent import Swarm


observability = Agent(
    name="observability",
    system_prompt=(
        "You focus on telemetry evidence. Hand off when another specialty "
        "is needed."
    ),
)

architect = Agent(
    name="architect",
    system_prompt=(
        "You reason about AWS architecture and dependencies. Separate "
        "documented behavior from incident evidence."
    ),
)

reviewer = Agent(
    name="reviewer",
    system_prompt=(
        "You challenge unsupported root-cause claims and finish with the "
        "smallest useful next diagnostic step."
    ),
)

swarm = Swarm(
    [observability, architect, reviewer],
    max_handoffs=5,
    max_iterations=8,
    execution_timeout=120.0,
    node_timeout=60.0,
)

result = swarm(
    "payments-api has intermittent 5xx errors and elevated latency. "
    "Collaborate to identify the strongest evidence and next diagnostic step."
)

print(result)
