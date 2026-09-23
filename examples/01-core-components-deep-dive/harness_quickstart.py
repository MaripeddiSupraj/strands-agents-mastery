from strands_harness import create_harness


agent = create_harness()

result = agent(
    "Explain what evidence you would gather first for a payments-api "
    "latency incident. Keep it concise."
)

print(result)
