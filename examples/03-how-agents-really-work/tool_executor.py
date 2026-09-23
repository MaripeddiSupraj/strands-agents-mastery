import time

from strands import Agent, tool
from strands.tools.executors import ConcurrentToolExecutor, SequentialToolExecutor


@tool
def get_latency() -> str:
    """Return synthetic latency evidence."""
    time.sleep(1)
    return "payments-api p95 latency: 820 ms"


@tool
def get_error_rate() -> str:
    """Return synthetic error-rate evidence."""
    time.sleep(1)
    return "payments-api 5xx rate: 4.8%"


def run(executor, label: str) -> None:
    agent = Agent(
        tools=[get_latency, get_error_rate],
        tool_executor=executor,
    )
    started = time.perf_counter()
    result = agent(
        "Gather latency and error-rate evidence for payments-api. "
        "Use both tools before summarizing."
    )
    print(f"\n{label}: {time.perf_counter() - started:.2f}s")
    print(result)


run(ConcurrentToolExecutor(), "concurrent")
run(SequentialToolExecutor(), "sequential")
