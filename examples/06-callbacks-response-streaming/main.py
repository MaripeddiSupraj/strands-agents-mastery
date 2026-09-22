import asyncio

from strands import Agent, tool


@tool
def get_service_status(service: str) -> str:
    """Return demo service status."""
    return {"payments-api": "degraded"}.get(service.strip().lower(), "unknown")


agent = Agent(tools=[get_service_status], callback_handler=None)


async def main():
    async for event in agent.stream_async(
        "Check payments-api and explain the next safe diagnostic step."
    ):
        if "data" in event:
            print(event["data"], end="", flush=True)


asyncio.run(main())
