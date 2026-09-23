from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent


@tool
def read_cloudwatch_fixture(service: str) -> str:
    """Synthetic read-only telemetry fixture."""
    if service.strip().lower() != "payments-api":
        return "no fixture"
    return (
        "10:12 UTC: p95 latency increased; 10:13 UTC: 5xx increased; "
        "no CPU saturation evidence in this fixture."
    )


@tool
def read_aws_docs_fixture(topic: str) -> str:
    """Synthetic docs fixture used before wiring the real MCP server."""
    return (
        "AWS service documentation should be queried for authoritative "
        "behavior. Documentation does not prove the current incident cause."
    )


observability = Agent(
    name="observability",
    system_prompt=(
        "Use telemetry evidence only. Separate observed facts from hypotheses."
    ),
    tools=[read_cloudwatch_fixture],
    context_manager="auto",
)

docs = Agent(
    name="aws-docs",
    system_prompt=(
        "Explain documented AWS behavior and never present documentation as "
        "proof of the current incident root cause."
    ),
    tools=[read_aws_docs_fixture],
    context_manager="auto",
)

ALLOWED = {"investigate_cloudwatch", "research_aws_docs"}


def block_unexpected_tool(event: BeforeToolCallEvent) -> None:
    name = event.tool_use["name"]
    if name not in ALLOWED:
        event.cancel_tool = f"Tool {name!r} is not allowed in this runtime."


commander = Agent(
    system_prompt=(
        "You are the incident commander. Evidence before root-cause claims. "
        "Separate facts, hypotheses and unknowns. Never claim remediation."
    ),
    tools=[
        observability.as_tool(
            name="investigate_cloudwatch",
            description="Investigate current read-only telemetry evidence.",
        ),
        docs.as_tool(
            name="research_aws_docs",
            description="Research authoritative AWS service behavior.",
        ),
    ],
    context_manager="auto",
)

commander.add_hook(block_unexpected_tool)

result = commander(
    "INC-2841: payments-api latency and 5xx increased after 10:12 UTC. "
    "Gather evidence and recommend the next safe diagnostic step.",
    limits={"turns": 8, "output_tokens": 3000, "total_tokens": 30000},
)

print(result)
print("Stop reason:", result.stop_reason)
print("Metrics:", result.metrics.get_summary())
