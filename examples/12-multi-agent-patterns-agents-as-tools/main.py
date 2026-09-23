from strands import Agent, tool


@tool
def get_service_status(service: str) -> str:
    """Return synthetic current telemetry status."""
    return {"payments-api": "degraded with elevated 5xx"}.get(
        service.strip().lower(), "unknown"
    )


@tool
def lookup_runbook(topic: str) -> str:
    """Return a small synthetic runbook entry."""
    return (
        "For 5xx + latency, first correlate errors with dependency latency "
        "before changing capacity."
    )


observability = Agent(
    name="observability",
    system_prompt="You investigate current evidence and never invent metrics.",
    tools=[get_service_status],
)

docs = Agent(
    name="runbook",
    system_prompt="You research operational guidance and distinguish it from evidence.",
    tools=[lookup_runbook],
)

commander = Agent(
    system_prompt=(
        "You are the incident commander. Delegate current evidence to "
        "observability and procedural guidance to runbook. Separate facts "
        "from hypotheses."
    ),
    tools=[
        observability.as_tool(
            name="investigate_observability",
            description="Investigate current service evidence.",
        ),
        docs.as_tool(
            name="research_runbook",
            description="Research operational guidance.",
        ),
    ],
)

print(
    commander(
        "payments-api has elevated latency and 5xx errors. "
        "Investigate and recommend the next diagnostic step."
    )
)
