# Start a container named "agent-workspace" first.
# This lab intentionally does not create or privilege the container for you.

from strands import Agent
from strands.sandbox.docker import DockerSandbox


sandbox = DockerSandbox(
    "agent-workspace",
    working_dir="/workspace",
    user="1000:1000",
)

agent = Agent(sandbox=sandbox)

print(
    agent(
        "List files in /workspace and summarize what you can see. "
        "Do not modify anything."
    )
)
