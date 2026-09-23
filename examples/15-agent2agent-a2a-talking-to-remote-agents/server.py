from strands import Agent
from strands.multiagent.a2a import A2AServer


def create_agent(context_id: str) -> Agent:
    return Agent(
        name="Security Specialist",
        description="Reviews authentication-related incident evidence.",
        system_prompt=(
            "You are a remote security specialist. Given incident evidence, "
            "identify the next authentication/security evidence to gather. "
            "Do not claim access to systems you have not queried."
        ),
        callback_handler=None,
    )


server = A2AServer(
    agent_factory=create_agent,
    host="127.0.0.1",
    port=9000,
)

server.serve()
