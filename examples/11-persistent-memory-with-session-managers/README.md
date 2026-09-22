# Example 11 — Persistent Memory with Session Managers

## Goal

Persist an incident, terminate the process, and resume it later.

## Run

First turn:

```bash
pip install strands-agents
python main.py first
```

Then run a new process:

```bash
python main.py resume
```

The local filesystem is for learning. Horizontally scaled production services need an appropriate shared/durable store.
