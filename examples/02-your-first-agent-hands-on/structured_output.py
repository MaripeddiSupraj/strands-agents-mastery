from pydantic import BaseModel, Field
from strands import Agent


class IncidentSummary(BaseModel):
    service: str = Field(description="Affected service")
    status: str = Field(description="Observed or stated status")
    next_step: str = Field(description="Recommended next diagnostic step")


agent = Agent()

result = agent(
    "payments-api is degraded. We do not yet know the root cause. "
    "Return a concise incident summary.",
    structured_output_model=IncidentSummary,
)

summary: IncidentSummary = result.structured_output
print(summary.model_dump_json(indent=2))
