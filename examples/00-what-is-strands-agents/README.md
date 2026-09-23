# Example 00 — What Is Strands Agents?

## Goal

See the smallest useful difference between one model call and a tool-using Agent.

## Run

```bash
pip install strands-agents
python main.py
```

Observe that the model may request `get_service_status`, but only the application decides that this capability exists.
