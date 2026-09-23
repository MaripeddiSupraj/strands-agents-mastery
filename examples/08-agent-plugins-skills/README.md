# Example 08 — Agent Plugins & Skills

## Goal

Package the incident-response procedure as a Skill instead of bloating the top-level prompt.

## Run

```bash
pip install strands-agents
python main.py
```

Observe that the Skill provides reusable instructions. It does **not** create new permissions or tools.
