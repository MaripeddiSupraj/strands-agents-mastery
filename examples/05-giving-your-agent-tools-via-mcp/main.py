from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient


docs_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"],
        )
    )
)

agent = Agent(tools=[docs_mcp])

result = agent(
    "Find authoritative AWS documentation that explains throttling. "
    "Explain the documented behavior, but do not claim it is the root cause "
    "of my payments-api incident without telemetry evidence."
)

print(result)
