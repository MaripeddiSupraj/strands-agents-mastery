# Example 16 — Evaluating Agents

## Goal

Turn manual incident prompts into a repeatable evaluation experiment.

## Install

```bash
pip install strands-agents-evals strands-agents
```

## Run

```bash
python basic_eval.py
```

The built-in `OutputEvaluator` uses a judge model by default. Pin provider/model config for controlled comparisons and keep deterministic authorization tests outside judge-model evals.
