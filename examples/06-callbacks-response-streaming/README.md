# Example 06 — Callbacks & Response Streaming

## Goal

Stream a live incident response and see partial output before the invocation finishes.

## Run

```bash
pip install strands-agents
python main.py
```

Measure time to first useful output separately from total task duration. Do not forward every raw internal event to an end user in production.

## Experimental lab — BidiAgent

BidiAgent is currently experimental and Python-only.

Install the realtime/audio extras required by the current Strands Bidi docs, including the platform audio dependency for microphone/speaker I/O, then run:

```bash
python bidi_voice.py
```

Treat this as an experimental lab, not a production API stability guarantee.
