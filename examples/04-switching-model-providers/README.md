# Example 04 — Switching Model Providers

## Goal

Run the **same prompt and tool** with different providers. Change only the model.

## Install

Bedrock is the default:

```bash
pip install strands-agents
```

Optional providers:

```bash
pip install 'strands-agents[openai]'
pip install 'strands-agents[anthropic]'
```

## Run

```bash
MODEL_PROVIDER=bedrock python main.py

OPENAI_API_KEY=... MODEL_PROVIDER=openai OPENAI_MODEL_ID=gpt-4o python main.py

ANTHROPIC_API_KEY=... MODEL_PROVIDER=anthropic ANTHROPIC_MODEL_ID=<current-model-id> python main.py
```

Compare tool selection, arguments, latency, total tokens and unsupported claims. Model IDs evolve; choose current IDs from the provider docs.

## Additional current lab — Model routing

Choose two model IDs currently available to your Bedrock account/region:

```bash
PRIMARY_BEDROCK_MODEL_ID=<id> \
BACKUP_BEDROCK_MODEL_ID=<id> \
python model_routing.py
```

Model IDs and regional availability change; use the current provider docs rather than freezing course values.
