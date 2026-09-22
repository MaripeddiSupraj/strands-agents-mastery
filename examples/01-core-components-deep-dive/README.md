# Example 01 — Core Components Deep Dive

## Goal

Map the main SDK surfaces onto one tiny incident Agent.

## Run

```bash
pip install strands-agents
python main.py
```

Inspect the registered tools, final stop reason, and metrics. Keep the mental model: Agent != model; the Agent owns model, tools, context, hooks/session policy and the loop.
