# Lesson 03 — How Agents Really Work

Strands Agents Mastery → Phase 1 — Core Agent Mechanics

A production agent is not “one smart model call.” It is a controlled event loop. If you understand that loop, almost every later Strands feature becomes easier to reason about: tools, hooks, retries, context management, multi-agent orchestration, evaluation, and observability all sit somewhere around it.

This lesson goes deeper than the happy path.

## Map of this lesson

- The loop, step by step
- What a turn means
- Stop reasons
- Per-invocation budgets
- Why token limits are soft at turn boundaries
- Cancellation
- Concurrency and idempotency
- Model retries and exponential backoff
- Local execution traces and metrics
- A production loop policy
- Tests to write before adding more capabilities


## Recommended hands-on example — Payments API Incident Assistant

> **Build today:** Trace one complete agent loop around a safe `get_service_status` tool.
>
> **Run:** `Check payments-api. If it is degraded, tell me the next diagnostic step without inventing a root cause.`
>
> **Expected flow:** user → model → `get_service_status("payments-api")` → tool result → model → final answer.
>
> **Observe:** the number of model turns, the tool call, total tokens, latency, and the final `stop_reason`.
>
> **Why this example:** it makes the agent loop visible. Do not move on until you can point to every model call and tool call in the trace.

Keep this same incident assistant for later lessons. Each lesson will add one production capability instead of starting from a completely different demo.


## 1. The core loop

A useful mental model is:

    receive user input
            ↓
    build model request
            ↓
       call model
            ↓
      inspect result
       ↙        ↘
    answer      tool request
      ↓             ↓
    stop       execute tool(s)
                    ↓
              append results
                    ↓
              next loop turn

The model is deciding what it wants to do. Strands owns the mechanics that interpret that decision and continue the loop.

That means an “agent request” may contain multiple model calls and multiple tool calls before you receive the final answer.

## 2. One invocation can contain many turns

Suppose the user asks:

    “Find the latest status of service A, compare it with service B,
    then explain which dependency is causing the incident.”

A possible execution is:

    Turn 1:
      model → call status(A)

    Tool:
      status(A) → degraded

    Turn 2:
      model → call status(B)

    Tool:
      status(B) → healthy

    Turn 3:
      model → call dependency_map(A)

    Tool:
      dependency_map(A) → database-x

    Turn 4:
      model → final explanation

One user request produced four model cycles.

This is why agent cost and latency must be reasoned about per invocation, not per prompt.

## 3. Stop reasons are part of your application contract

The current Strands agent loop documents several stop reasons.

Important ones include:

- end_turn — normal completion;
- tool_use — model requested tool execution, so the loop continues;
- cancelled — external cancellation;
- limit_turns — invocation turn budget reached;
- limit_total_tokens — total token budget reached;
- limit_output_tokens — output token budget reached;
- max_tokens — a model response itself hit its max-token boundary;
- stop_sequence — configured stop sequence reached;
- content_filtered — safety filter blocked content;
- guardrail_intervened — guardrail stopped generation.

Do not treat every non-exception result as “success.”

Your API should deliberately map stop reasons to business outcomes.

For example:

| Stop reason | Possible application behavior |
| --- | --- |
| end_turn | Return normal answer |
| limit_turns | Return bounded/incomplete status, optionally allow retry |
| limit_total_tokens | Ask user to narrow scope or resume with approval |
| cancelled | Return client-cancelled/request-timeout result |
| content_filtered | Return policy-safe response |
| guardrail_intervened | Return safe response and audit event |
| max_tokens | Treat as failed/incomplete generation |

The exact business mapping is yours, but it should exist.

## 4. Put a budget on every invocation

Current Strands supports per-invocation limits for turns, output tokens, and total tokens.

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent()

result = agent(
    "Summarize this document",
    limits={
        "turns": 5,
        "output_tokens": 2000,
        "total_tokens": 10000,
    },
)

if result.stop_reason == "limit_turns":
    print("Hit turn budget")
elif result.stop_reason == "limit_total_tokens":
    print("Hit token budget")
~~~

The same limits parameter is documented for invoke_async and stream_async.

All caps are optional, and the Python API requires positive integer values.

## 5. Why limits are not hard mid-call kill switches

A subtle but important current behavior: invocation limits are checked at loop-turn boundaries.

That means one model response may push cumulative token usage past the configured cap before Strands stops the next turn.

Likewise, tools requested by the previous model turn run before the next budget check.

Think of it like this:

    top of turn → check budget
        ↓
      model call
        ↓
      tools run
        ↓
    top of next turn → check budget again

Therefore:

- invocation token caps are end-to-end control, but soft by one turn;
- model max_tokens still matters for a single response;
- expensive tools need their own quotas/timeouts;
- destructive tools should not rely on “the turn limit will stop it.”

## 6. A production budget should have four layers

### 6.1 Turn budget

Controls repeated model/tool cycles.

Use it to prevent runaway loops.

### 6.2 Token budget

Controls total model consumption for the invocation.

Use separate output limits where response size matters.

### 6.3 Tool budget

A tool may be expensive even when token usage is small.

Examples:

- an observability search scanning many GB;
- a SaaS API charged per request;
- infrastructure operations;
- a database query with expensive fan-out.

Enforce tool-specific limits in application code or lifecycle hooks.

### 6.4 Wall-clock deadline

A request can remain within token limits and still take too long because tools block or retries back off.

Your hosting layer should have an overall request deadline.

For Python, current Strands supports agent.cancel() and caller-owned cancellation signaling. A tool already running must cooperate with cancellation or it may finish before cancellation is observed.

## 7. Cancellation is cooperative

Current Strands checks cancellation around the loop and between tool calls. Once a tool callback is already running, the SDK cannot magically terminate arbitrary Python code safely.

So this is not enough:

    API timeout = 30 seconds

if a tool internally performs a 5-minute network call without its own timeout.

A robust chain is:

    HTTP request deadline
       ↓
    agent cancellation
       ↓
    tool receives/observes deadline
       ↓
    downstream HTTP/database/cloud call timeout

Every layer needs a bounded wait.

## 8. External cancellation signal

The current Python Agent API accepts a caller-owned cancel_signal for invocation methods.

The reference documents it as useful for cases such as:

- client disconnect;
- request lifecycle cancellation;
- timeout owned by the calling service.

The signal and agent.cancel() are observed independently.

Because exact integration depends on your web framework, use the current API reference when wiring framework-specific cancellation rather than copying an old framework example.

## 9. Concurrency: one Agent instance is one conversation

Current Python Agent instances maintain mutable internal conversation state.

By default, overlapping invocations on the same instance are not safe. The SDK raises ConcurrencyException when a different invocation starts while another is already running.

This is a good default.

Why?

Imagine:

    request A adds user message A
    request B adds user message B
    model A responds
    model B responds

If those operations interleave into one history, both users can affect the same conversation state.

Production rule:

> Do not share one stateful Agent instance across unrelated concurrent user conversations.

Create a clear ownership model for Agent instances and session IDs.

## 10. Idempotency prevents duplicate work

Network clients retry. Load balancers retry. Job workers retry. A user double-clicks.

If an identical logical request reaches the same Agent while the original is still in flight, current Strands can deduplicate it with idempotency_token.

**Code sample — verified**

~~~python
result = agent(
    "Process order 1234",
    idempotency_token="order-1234",
)
~~~

If another in-flight invocation uses the same token, the duplicate waits and receives the original AgentResult rather than starting the work again.

If the token differs while that Agent instance is busy, normal concurrency protection applies and ConcurrencyException is raised.

Important: idempotency at the Agent invocation layer does not automatically make every downstream side effect idempotent.

A payment/refund/update tool still needs its own idempotency key and safe retry semantics.

## 11. Do not use a prompt as your idempotency design

The docs note that any stable equatable identifier can be used as a token, including a request UUID or logical ID.

For enterprise workloads, prefer a business/request identifier you control rather than raw prompt text.

Good:

    incident-INC123-analysis-v2

Poor:

    "please analyze this"

You want traceability and predictable retry grouping.

## 12. Model retries happen inside the reliability story

Models are network services. Throttling and transient failures happen.

Current Strands automatically retries retryable model throttling failures by default.

The documented Python default is:

- 6 total attempts;
- first retry after 4 seconds;
- exponential backoff;
- configurable maximum delay.

That default can create a surprisingly long request when the provider is throttled.

Latency SLOs therefore need to account for retry policy.

## 13. Configure retry strategy intentionally

**Code sample — verified**

~~~python
from strands import Agent, ModelRetryStrategy

agent = Agent(
    retry_strategy=ModelRetryStrategy(
        max_attempts=3,
        initial_delay=2,
        max_delay=60,
    )
)
~~~

The current docs define max_attempts as total attempts including the first call.

Setting max_attempts=1 disables model retries.

Do not choose retry counts independently of:

- your external request timeout;
- provider quotas;
- user-facing latency SLO;
- cost budget;
- upper-layer retry behavior.

Otherwise you can create retry multiplication:

    load balancer retries 3×
      × app retries 3×
      × model retries 6×
      = potentially many attempts

## 14. Retry only failures that are actually retryable

The current default retry strategy is deliberately narrow around model throttling.

That is healthy.

Do not retry:

- invalid credentials;
- invalid model configuration;
- policy blocks;
- malformed tool input;
- deterministic authorization denial.

Retries turn deterministic errors into slow deterministic errors.

## 15. Trace the loop locally

Strands exposes local execution traces even without configuring an external OpenTelemetry exporter.

The current metrics documentation describes each trace as a timing hierarchy containing cycles plus model/tool child operations.

**Code sample — verified**

~~~python
from strands import Agent
from strands_tools import calculator

agent = Agent(tools=[calculator])
result = agent("What is 15 * 8 + 42?")

print(result.metrics.get_summary())
~~~

The summary includes execution information that helps answer:

- how many cycles occurred;
- how long each cycle took;
- which tools ran;
- where latency accumulated.

The current SDK also exposes local traces directly on AgentResult.

## 16. Add OpenTelemetry visibility

For full tracing/export, use the SDK telemetry layer.

**Code sample — verified**

~~~python
from strands.telemetry import StrandsTelemetry

StrandsTelemetry().setup_console_exporter()
~~~

This is a development-friendly way to see spans.

In production:

- export to an approved OpenTelemetry collector/backend;
- attach correlation attributes such as request/session identifiers that are safe to log;
- never use raw customer prompts as high-cardinality metric labels;
- apply PII/secret redaction before exporting sensitive content.

Lesson 17 builds this properly.

## 17. Metrics to review for every new tool

After introducing a tool, compare at least:

- total tokens before/after;
- total latency;
- number of loop cycles;
- tool count;
- tool success/error rate;
- tool duration;
- final stop reason.

A tool can improve answer quality while harming cost or latency. That is a product tradeoff, not a hidden technical detail.

## 18. A safer invocation wrapper

The following is intentionally course-authored. It uses verified AgentResult behavior but is not copied line-for-line from the docs.

**Code sample — illustrative**

~~~python
from dataclasses import dataclass
from strands import Agent

@dataclass
class SafeAgentResponse:
    status: str
    text: str
    stop_reason: str
    total_tokens: int | None

def invoke_bounded(agent: Agent, prompt: str, request_id: str) -> SafeAgentResponse:
    result = agent(
        prompt,
        idempotency_token=request_id,
        limits={
            "turns": 6,
            "output_tokens": 2500,
            "total_tokens": 12000,
        },
    )

    usage = result.metrics.accumulated_usage
    total_tokens = usage.get("totalTokens")

    if result.stop_reason == "end_turn":
        status = "completed"
    elif result.stop_reason in {
        "limit_turns",
        "limit_total_tokens",
        "limit_output_tokens",
    }:
        status = "budget_exhausted"
    elif result.stop_reason == "cancelled":
        status = "cancelled"
    elif result.stop_reason in {
        "content_filtered",
        "guardrail_intervened",
    }:
        status = "policy_stopped"
    else:
        status = "incomplete"

    return SafeAgentResponse(
        status=status,
        text=str(result),
        stop_reason=result.stop_reason,
        total_tokens=total_tokens,
    )
~~~

This wrapper makes an architectural idea explicit: loop termination becomes application state rather than an ignored SDK detail.

Before production, adapt output extraction to your API contract and test the exact AgentResult representation used by your pinned SDK version.

## 19. Testing the loop

Your test suite should have distinct layers.

### Unit tests

Test pure code around:

- stop-reason mapping;
- budget configuration;
- request-ID generation;
- tool validation;
- retryable versus non-retryable application errors.

### Integration tests

Against a real model/provider in a controlled account:

- simple end_turn;
- one tool call;
- multiple tool calls;
- cancellation;
- expected auth denial;
- timeout behavior.

### Behavioral evaluation

Later use Strands Evals to check:

- correct tool selected;
- correct parameters;
- goal achieved;
- no invented result after tool failure.

## 20. Failure injection exercise

Create a development-only tool that sleeps for a controlled amount of time and another that returns a controlled error.

Observe:

1. how tool latency appears in metrics;
2. what cancellation does;
3. whether your outer request timeout is actually enforced;
4. how the agent explains the tool failure;
5. whether it attempts an unsafe fallback.

Do not use production dependencies for failure-injection practice.

## 21. Cost exercise

Run the same task with:

- turns=2;
- turns=5;
- turns=10.

Capture:

- final stop reason;
- total tokens;
- wall-clock time;
- answer quality.

The lesson is not “higher is better.” It is to learn how task quality changes as you allocate more reasoning/tool budget.

## 22. Production rules from this lesson

1. Every invocation gets a budget.
2. Every network/tool call gets a timeout.
3. Stop reasons become API/application state.
4. One Agent instance does not serve unrelated concurrent conversations.
5. Retry policy is part of latency policy.
6. Side-effect tools need downstream idempotency too.
7. Traces and metrics are inspected while developing, not after launch.
8. A budget limit is not an authorization boundary.

## Sources checked

- https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/
- https://strandsagents.com/docs/user-guide/concepts/agents/retry-strategies/
- https://strandsagents.com/docs/api/python/strands.agent.agent/
- https://strandsagents.com/docs/api/python/strands.types.exceptions/
- https://strandsagents.com/docs/user-guide/observability-evaluation/metrics/
- https://strandsagents.com/docs/user-guide/deploy/operating-agents-in-production/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 04 — Switching Model Providers](04-switching-model-providers.md). We will keep the harness stable while changing Bedrock, Anthropic, OpenAI, Ollama, and other provider backends, then define how an enterprise team evaluates that change.

Back to the [course README](../README.md).
