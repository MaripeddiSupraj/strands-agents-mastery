from strands import Agent


collector = Agent(
    system_prompt=(
        "Collect only the incident facts supplied to you. "
        "Do not invent evidence."
    ),
    callback_handler=None,
)
analyst = Agent(
    system_prompt=(
        "Analyze incident evidence. Separate facts, hypotheses and unknowns."
    ),
    callback_handler=None,
)
writer = Agent(
    system_prompt=(
        "Write a concise report with Evidence, Hypotheses, Unknowns, "
        "and Next Step."
    ),
)


def process_workflow(incident: str):
    evidence = collector(f"Collect evidence for: {incident}")
    analysis = analyst(f"Analyze this evidence: {evidence}")
    return writer(f"Write the incident report from this analysis: {analysis}")


print(
    process_workflow(
        "INC-2841: payments-api p95 latency and 5xx increased at 10:12 UTC."
    )
)
