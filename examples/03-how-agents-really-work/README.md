# Example 03 — How Agents Really Work

## Goal

Trace one complete model → tool → model loop and put a hard budget around it.

## Run

```bash
pip install strands-agents
python main.py
```

## Observe

- `stop_reason`
- cycle/tool metrics
- total tokens
- console OpenTelemetry spans
- what happens if you lower `turns`

## Additional current lab — Tool executors

```bash
python tool_executor.py
```

Compare concurrent (default) and sequential execution. Parallel behavior still depends on the model returning multiple tool calls in one turn.
