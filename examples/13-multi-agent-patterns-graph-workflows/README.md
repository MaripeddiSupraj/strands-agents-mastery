# Example 13 — Multi-Agent Graph Workflows

## Goal

Make the allowed incident workflow explicit with `GraphBuilder`.

## Run

```bash
pip install strands-agents
python main.py
```

The graph is deterministic between nodes: collect → analyze → report. The Agents still reason inside each node.

## Additional current lab — Workflow

```bash
python workflow.py
```

Use Workflow for a repeatable sequence/DAG. Compare it with the Graph example in this same folder.
