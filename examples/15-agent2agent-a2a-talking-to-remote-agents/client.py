from strands.agent.a2a_agent import A2AAgent


security_agent = A2AAgent(
    endpoint="http://localhost:9000",
    name="security-specialist",
    timeout=60,
)

result = security_agent(
    "INC-2841 has repeated authentication failures. "
    "What security evidence should the incident commander check next?"
)

print(result.message)
