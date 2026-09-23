# Example 17 — Observability: Traces, Metrics & Logs

## Goal

Explain why an incident request was slow by inspecting traces and AgentResult metrics.

## Run

```bash
pip install strands-agents
python main.py
```

The console exporter is for local learning. Production should use an approved OTLP path with data-redaction policy.
