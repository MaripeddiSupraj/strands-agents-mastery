from pathlib import Path

from strands import Agent, AgentSkills


skills_dir = Path(__file__).parent / "skills"
incident_skills = AgentSkills(skills=str(skills_dir))

agent = Agent(plugins=[incident_skills])

result = agent(
    "INC-2841: payments-api latency increased after 10:12 UTC. "
    "Use the incident-response procedure and tell me how to investigate."
)

print(result)
