from strands import Agent, tool


@tool
def query_logs(service: str) -> str:
    """Return intentionally verbose synthetic logs for context testing."""
    return "\n".join(
        f"{service} event={i} status=500 dependency=inventory-api"
        for i in range(250)
    )


agent = Agent(
    tools=[query_logs],
    context_manager="auto",
)

first = agent(
    "Query payments-api logs and identify the strongest repeated signal. "
    "Do not invent a root cause."
)
print(first)
print("First metrics:", first.metrics.get_summary())

second = agent(
    "Using only the important evidence from our investigation, "
    "what is the smallest useful next diagnostic step?"
)
print(second)
print("Second metrics:", second.metrics.get_summary())
