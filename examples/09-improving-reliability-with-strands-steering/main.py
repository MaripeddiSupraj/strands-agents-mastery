from strands import Agent, tool
from strands.vended_plugins.steering import LLMSteeringHandler


@tool
def query_logs(window_minutes: int) -> str:
    """Query synthetic payments-api logs for a bounded time window."""
    if window_minutes > 15:
        return "Query too broad: reduce the window to 15 minutes or less."
    return f"payments-api: 5xx spike found in the last {window_minutes} minutes"


handler = LLMSteeringHandler(
    system_prompt="""
You guide an incident investigator toward efficient evidence gathering.

Rules:
- Prefer a narrow log query before a broad scan.
- If query_logs would use more than 15 minutes, guide the agent to reduce it.
- If a tool has already failed, do not repeat the same call unchanged.
"""
)

agent = Agent(
    tools=[query_logs],
    plugins=[handler],
)

result = agent(
    "Investigate payments-api errors from the last hour. "
    "Use logs, but avoid wasteful repeated queries."
)

print(result)
