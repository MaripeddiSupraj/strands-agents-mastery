# Example 09 — Improving Reliability with Strands Steering

## Goal

Use current Python Steering to provide just-in-time guidance before a wasteful tool call.

## Run

```bash
pip install strands-agents
python main.py
```

The current Python API uses `LLMSteeringHandler` as a plugin. Its built-in ledger gives the steering model tool-call context.

Steering guides behavior; authorization still belongs in deterministic policy/IAM.
