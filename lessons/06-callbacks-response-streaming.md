# Lesson 06 — Callbacks & Response Streaming

Strands Agents Mastery → Phase 2 — Tools & Interaction

Streaming improves perceived responsiveness and lets your application observe an agent while it works. It does not make the model cheaper, and it does not make every intermediate event safe to show to an end user.

This lesson separates three ideas:

- the final AgentResult;
- the stream of incremental events;
- Python callback handlers.

## Map of this lesson

- Why stream
- Python async iterators
- TypeScript streaming distinction
- Python callback handlers
- Event filtering
- Tool-progress visibility
- Backpressure and disconnects
- Security and PII
- Observability
- Testing streams


## Recommended hands-on example — Stream an incident investigation to the user

> **Build today:** Stream progress from the same incident assistant while it performs a documentation/tool lookup.
>
> **Run:** `Investigate the payments-api throttling symptom and explain the next safe diagnostic step.`
>
> **User experience to aim for:** show a safe status such as “Checking AWS documentation…” quickly, stream the final explanation as it becomes available, then emit one clear completion event.
>
> **Observe:** time to first useful output, tool-start/tool-end timing, final task duration, and what internal events you intentionally *do not* expose to the browser.
>
> **Why this example:** learners can see that streaming is an interface/UX concern around the same agent loop—not a different kind of agent.

Do not forward raw MCP/tool payloads just because they appear in the event stream.


## 1. Non-streaming invocation

The ordinary call waits until the agent invocation completes.

    request
      ↓
    agent loop runs
      ↓
    final AgentResult

This is easiest to reason about, but a multi-tool task can feel unresponsive.

## 2. Streaming invocation

Streaming exposes events while the loop runs:

    request
      ↓
    text delta
    text delta
    tool-use event
    tool progress
    more text
    ...
      ↓
    completion

Your UI can start rendering before the full task is done.

But remember:

> An intermediate stream event is not the final business outcome.

A later tool may fail, a guardrail may intervene, or the invocation may be cancelled.

## 3. Python stream_async

Current Python Strands exposes stream_async as the asynchronous streaming counterpart to invoke_async.

**Code sample — verified**

~~~python
import asyncio
from strands import Agent

agent = Agent(callback_handler=None)

async def process_stream():
    async for event in agent.stream_async("Explain DNS simply."):
        if "data" in event:
            print(event["data"], end="", flush=True)

asyncio.run(process_stream())
~~~

Setting callback_handler=None prevents the default callback behavior from separately printing output while you consume the iterator yourself.

## 4. Streaming with tool visibility

The current quickstart shows tool-use information appearing in stream events.

**Code sample — verified**

~~~python
import asyncio
from strands import Agent
from strands_tools import calculator

agent = Agent(
    tools=[calculator],
    callback_handler=None,
)

async def process_streaming_response():
    prompt = "What is 25 * 48 and explain the calculation"

    async for event in agent.stream_async(prompt):
        if "data" in event:
            print(event["data"], end="", flush=True)
        elif "current_tool_use" in event and event["current_tool_use"].get("name"):
            print(
                f"\n[Tool use delta for: "
                f"{event['current_tool_use']['name']}]"
            )

asyncio.run(process_streaming_response())
~~~

For a real user interface, decide whether a tool name is appropriate to expose. Internal tool names can reveal architecture or sensitive capabilities.

## 5. TypeScript distinction

Current Strands documentation does not support Python-style callback handlers in TypeScript.

TypeScript uses:

- agent.stream() for async streaming;
- hooks for lifecycle handling.

Do not try to port callback-handler code mechanically between SDKs.

## 6. Python callback handlers

A callback handler is a synchronous Python function invoked as agent events occur.

**Code sample — verified**

~~~python
from strands import Agent

def custom_callback_handler(**kwargs):
    if "data" in kwargs:
        print(kwargs["data"], end="", flush=True)

agent = Agent(callback_handler=custom_callback_handler)
agent("Explain what an agent loop is.")
~~~

The callback receives event fields through keyword arguments.

Use this for lightweight synchronous handling. For async web servers, the current docs recommend the async iterator approach.

## 7. Built-in callback-handler support

Current Python source exposes handlers such as PrintingCallbackHandler and CompositeCallbackHandler.

PrintingCallbackHandler is designed for stdout-style text/tool display.

CompositeCallbackHandler can fan one event stream into multiple synchronous handlers.

Use these when their exact behavior matches your need; do not build a production audit pipeline by scraping terminal output.

## 8. Streaming is presentation plus control data

The stream can include different categories of events:

- text data;
- tool-use information;
- lifecycle events;
- model streaming updates;
- tool streaming updates;
- completion state.

For a web client, define a stable application event contract instead of passing raw SDK dictionaries directly to the browser.

Example application events:

    answer.delta
    tool.started
    tool.completed
    request.completed
    request.failed

Then map Strands events internally.

That decouples your frontend from SDK event-shape changes.

## 9. Never dump every raw event to the user

A debugging handler that prints all event dictionaries can be useful locally.

It can be dangerous in production because events may contain:

- tool inputs;
- tool results;
- model output;
- identifiers;
- potentially sensitive user data.

Separate:

    developer diagnostic stream

from:

    user-facing progress stream

and apply redaction to both.

## 10. Reasoning data deserves special caution

Some model/provider events can carry reasoning-related fields.

Do not design your application around exposing hidden/internal reasoning or sensitive intermediate data.

A safe user-facing stream should focus on:

- approved text output;
- coarse tool/progress status;
- final result;
- user-action requests such as approval.

## 11. Tool progress versus tool result

Suppose a log-search tool streams:

    scanned 10%
    scanned 50%
    scanned 90%

That is progress.

The final tool result may still be:

    timeout / access denied / no evidence found

Do not interpret progress events as success.

Operationally, track separate states:

    started
    progress
    succeeded
    failed
    retried
    cancelled

## 12. Retried tools complicate streaming

Current hooks/API documentation notes an important behavior: if an AfterToolCall hook asks Strands to retry a tool, intermediate tool-stream events from the discarded attempt may already have been emitted.

Therefore streaming consumers should not assume:

    “I saw progress from attempt 1, therefore that attempt became the final result.”

Use IDs/attempt state in your application protocol where retries matter.

## 13. Client disconnect should become cancellation

A common production failure:

1. browser disconnects;
2. API server notices;
3. agent continues running for five minutes;
4. model/tool cost continues even though nobody will receive the answer.

Connect request cancellation to agent cancellation.

Lesson 03 covered Strands cancellation semantics. Your web framework should stop the agent and propagate deadlines to downstream tools.

Do not provide framework-specific code from memory; use your framework’s current disconnect/cancellation primitives and Strands current cancel_signal/cancel API.

## 14. Backpressure

A model can produce events faster than a slow client can consume them.

If you buffer forever:

- memory grows;
- latency grows;
- process can fail.

Design:

- bounded queue/buffer;
- appropriate transport buffering;
- slow-client policy;
- cancellation after disconnect;
- timeout.

Do not put an unbounded asyncio.Queue between Strands and a client in production.

## 15. Streaming does not reduce token cost

Streaming changes delivery timing.

The model still generates the tokens.

It may improve perceived latency:

    first token arrives sooner

while total generation time and total token billing remain similar for the same model output.

Measure:

- time to first approved output;
- total invocation duration;
- token use;
- tool durations.

## 16. Protect PII in the stream

A final response can be filtered/redacted before returning.

Streaming creates a harder question because data leaves incrementally.

If your compliance model requires output scanning before any sensitive token leaves the service, raw token streaming may be incompatible with that requirement.

Options include:

- buffer full model output, validate, then release;
- stream only coarse progress while final content is validated;
- use provider/model guardrail features where appropriate;
- redact tool data before it reaches model/output.

Security requirements determine streaming architecture.

## 17. A safer event adapter

This course-authored adapter forwards only an allowlisted subset.

**Code sample — illustrative**

~~~python
def to_public_event(event: dict) -> dict | None:
    if "data" in event:
        return {
            "type": "answer.delta",
            "text": event["data"],
        }

    current_tool = event.get("current_tool_use")
    if current_tool and current_tool.get("name"):
        return {
            "type": "tool.started",
            "tool": "approved-operation",
        }

    if event.get("complete"):
        return {
            "type": "request.completed",
        }

    return None
~~~

Notice that the adapter does not return arbitrary event fields or tool arguments.

In a real system, sanitize text as required by your data policy and map tool names to user-safe descriptions.

## 18. Callback handler should stay fast

Python callback handlers run synchronously in the event path.

Do not perform slow network calls directly inside every text-delta callback.

Bad design:

    each token
      → synchronous database write

Better:

- aggregate;
- enqueue bounded telemetry;
- sample;
- flush at safe lifecycle points.

Hooks are a better mechanism for many lifecycle-level behaviors; callbacks are convenient for stream presentation.

## 19. Observability for streams

Track two latency measurements:

### Time to first output

Useful for interactive UX.

### Time to completion

Useful for SLO/cost/throughput.

Also track:

- cancellation rate;
- client disconnect rate;
- tool-start to tool-complete duration;
- error after first byte was already sent.

The last point matters for HTTP APIs: after headers/body begin streaming, changing the HTTP status may no longer be possible. Your stream protocol needs an explicit failure event.

## 20. Testing streams

Test at least:

### Ordered content

Text deltas are assembled into expected content order.

### Tool event filtering

Sensitive arguments are not exposed.

### Disconnect

Client cancellation stops ongoing agent work.

### Error after partial output

Frontend receives a clear terminal failure event.

### Retry

Duplicate/progress events do not corrupt UI state.

### Large output

Buffering remains bounded.

## 21. Production checklist

- [ ] Raw SDK events are not passed directly to clients.
- [ ] Public event schema is versioned.
- [ ] Sensitive tool arguments/results are filtered.
- [ ] Client disconnect cancels agent work.
- [ ] Downstream tools have their own timeouts.
- [ ] Buffering is bounded.
- [ ] Final success/failure is explicit.
- [ ] Time-to-first-output and total duration are measured.
- [ ] Streaming compatibility with PII policy is documented.


## 16. Advanced/experimental: BidiAgent is a different streaming model

Standard `Agent.stream_async()` remains request/response streaming.

Current Strands also documents `BidiAgent` for persistent bidirectional connections used by realtime voice/audio and interruption-heavy experiences. Strands marks it **experimental** and Python-only at the time of this audit.

**Code sample — verified**

~~~python
import asyncio

from strands.experimental.bidi import BidiAgent, BidiAudioIO
from strands.experimental.bidi.models import BedrockNovaSonicModel

model = BedrockNovaSonicModel()
agent = BidiAgent(
    model=model,
    system_prompt="You are a concise incident-response voice assistant.",
)
audio_io = BidiAudioIO()

async def main():
    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()],
    )

asyncio.run(main())
~~~

Use BidiAgent only when persistent realtime streaming and interruptions are actual requirements.

Runnable experimental lab: [bidi_voice.py](../examples/06-callbacks-response-streaming/bidi_voice.py).

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/streaming/async-iterators/
- https://strandsagents.com/docs/user-guide/sdk/streaming/callback-handlers/
- https://strandsagents.com/docs/api/python/strands.handlers.callback_handler/
- https://strandsagents.com/docs/user-guide/sdk/quickstart/python/
- https://strandsagents.com/docs/api/python/strands.hooks.events/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 07 — Controlling Your Agent With Hooks](07-controlling-your-agent-with-hooks.md). Streaming observes the loop; hooks let application code participate in and control lifecycle behavior.

Back to the [course README](../README.md).
