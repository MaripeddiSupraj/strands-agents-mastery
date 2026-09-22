from strands import Agent
from strands.multiagent import GraphBuilder


collector = Agent(
    name="collector",
    system_prompt=(
        "Extract the incident symptom, affected service, time window and "
        "known evidence. Do not invent missing data."
    ),
)

analyst = Agent(
    name="analyst",
    system_prompt=(
        "Analyze the supplied incident evidence. Separate facts, hypotheses "
        "and unknowns."
    ),
)

reporter = Agent(
    name="reporter",
    system_prompt=(
        "Produce a concise incident report with Evidence, Hypotheses, "
        "Unknowns and Next Step."
    ),
)

builder = GraphBuilder()
builder.add_node(collector, "collect")
builder.add_node(analyst, "analyze")
builder.add_node(reporter, "report")
builder.add_edge("collect", "analyze")
builder.add_edge("analyze", "report")
builder.set_entry_point("collect")
builder.set_execution_timeout(120)

graph = builder.build()

result = graph(
    "INC-2841: payments-api latency and 5xx increased around 10:12 UTC."
)
print(result)
