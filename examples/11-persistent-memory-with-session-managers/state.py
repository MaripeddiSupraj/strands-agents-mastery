from strands import Agent, ToolContext, tool


@tool(context=True)
def whoami(tool_context: ToolContext) -> str:
    """Return trusted request identity from invocation state."""
    user_id = tool_context.invocation_state.get("user_id", "unknown")
    request_id = tool_context.invocation_state.get("request_id", "unknown")
    return f"user_id={user_id}, request_id={request_id}"


agent = Agent(
    tools=[whoami],
    state={"service": "payments-api", "environment": "staging"},
)

result = agent(
    "Who am I and which request is this?",
    invocation_state={
        "user_id": "operator-42",
        "request_id": "req-2841",
    },
)

print(result)
print("Agent state:", agent.state.get())
print("Invocation result state:", result.state)
