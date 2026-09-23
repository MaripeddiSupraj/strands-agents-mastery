# Example 15 — Agent2Agent (A2A)

## Goal

Move a specialist behind a real network/service boundary.

## Install

```bash
pip install 'strands-agents[a2a]'
```

## Run

Terminal 1:

```bash
python server.py
```

Terminal 2:

```bash
python client.py
```

The server uses `agent_factory`, the current recommended isolation pattern. A2A context IDs are protocol/session state, not authentication.
