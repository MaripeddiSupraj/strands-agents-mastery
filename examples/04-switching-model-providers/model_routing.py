import os

from strands import Agent
from strands.models import BedrockModel, ModelRouter


primary_model = BedrockModel(
    model_id=os.environ["PRIMARY_BEDROCK_MODEL_ID"],
)
backup_model = BedrockModel(
    model_id=os.environ["BACKUP_BEDROCK_MODEL_ID"],
)

router = ModelRouter(models=[primary_model, backup_model])

agent = Agent(model=router)

print(
    agent(
        "Explain the smallest safe next step for investigating a payments-api "
        "latency incident when no root cause is established yet."
    )
)
