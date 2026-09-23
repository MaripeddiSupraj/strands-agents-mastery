# Example 01 — Core Components Deep Dive

## Goal

Map the main SDK surfaces onto one tiny incident Agent.

## Run

```bash
pip install strands-agents
python main.py
```

Inspect the registered tools, final stop reason, and metrics. Keep the mental model: Agent != model; the Agent owns model, tools, context, hooks/session policy and the loop.

## Additional current lab — Strands Harness

```bash
pip install strands-harness
python harness_quickstart.py
```

Use this after understanding the component map so the assembled defaults do not feel magical.
