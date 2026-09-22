# Example 06 — Callbacks & Response Streaming

## Goal

Stream a live incident response and see partial output before the invocation finishes.

## Run

```bash
pip install strands-agents
python main.py
```

Measure time to first useful output separately from total task duration. Do not forward every raw internal event to an end user in production.
