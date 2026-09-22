# Example 07 — Controlling Your Agent With Hooks

## Goal

Prove that a deterministic hook can block a dangerous tool even if the model asks for it.

## Run

```bash
pip install strands-agents
python main.py
```

The `restart_production_service` function is deliberately fake. If you ever see `SHOULD NEVER RUN`, the lab failed.

In a real system, the stronger design is not to register unauthorized tools at all.
