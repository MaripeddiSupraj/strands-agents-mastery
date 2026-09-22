# Example 13 — Multi-Agent Graph Workflows

## Goal

Make the allowed incident workflow explicit with `GraphBuilder`.

## Run

```bash
pip install strands-agents
python main.py
```

The graph is deterministic between nodes: collect → analyze → report. The Agents still reason inside each node.
