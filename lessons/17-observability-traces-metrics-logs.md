# Lesson 17 — Observability: Traces, Metrics & Logs

Strands Agents Mastery → Phase 5 — Production Readiness

Traditional services are often debugged with:

    request
      → service
      → database/API
      → response

An Agent request can be:

    request
      → model
      → tool
      → model
      → specialist Agent
      → MCP tool
      → model
      → final response

Without traces, metrics, and logs, the only symptom may be:

    “The Agent was slow and gave a bad answer.”

That is not enough to operate a production system.

## Map of this lesson

- The three observability primitives
- Local AgentResult metrics
- OpenTelemetry tracing
- OTLP export
- Metrics export
- Logging
- Correlation IDs
- Multi-agent visibility
- Cost and SLO metrics
- PII and telemetry
- Sampling/cardinality
- Alerts and dashboards
- Incident debugging
- CI and deployment verification


## Recommended hands-on example — Debug one slow incident request from trace to tool

> **Build today:** Run the payments-api incident assistant with tracing/metrics enabled and investigate one intentionally slow request.
>
> **Question to answer from telemetry:** `Why did this request take 12 seconds?`
>
> **Trace the path:** Incident Commander → model call → observability specialist → MCP/CloudWatch tool → model call → final synthesis.
>
> **Observe:** model latency, tool latency, cycle count, token usage, retries, specialist calls, final `stop_reason`, and one correlation ID across the request.
>
> **Why this example:** observability becomes useful when it answers a concrete operational question, not when it merely proves that spans exist.

Do not solve observability by exporting every prompt and raw log result. Make the request explainable without creating a sensitive-data archive.


## 1. Traces, metrics, and logs answer different questions

### Trace

    What happened in this one request?

Example:

    model 1.2s
      → get_logs 4.7s
      → model 0.9s
      → security_agent 3.1s

### Metric

    Is this behavior healthy across many requests?

Example:

    p95 latency = 8.3s
    tool error rate = 1.7%
    avg total tokens = 8,200

### Log

    What detailed event/error did the SDK or application emit?

Example:

    AccessDenied calling CloudWatch GetQueryResults

Do not force one primitive to do all three jobs.

## 2. Strands already records per-invocation metrics

Current Strands AgentResult metrics include categories such as:

- input/output/total tokens;
- cache-related usage where available;
- latency/execution timing;
- tool calls and tool execution times;
- event-loop cycle counts/durations.

You do not need an external observability backend to inspect these during development.

## 3. Read metrics from AgentResult

**Code sample — verified**

The current metrics API exposes accumulated usage, cycle durations, and tool metrics.

~~~python
from strands import Agent

agent = Agent()
result = agent("Explain the difference between latency and throughput.")

print(result.metrics.accumulated_usage)
print(result.metrics.cycle_durations)
print(result.metrics.tool_metrics)
~~~

Treat metric fields defensively across providers. Not every model/provider necessarily reports every optional usage field identically.

## 4. Use local summaries while developing

Current Strands metrics also provide local execution summary/trace views.

The exact summary format is intended for analysis/debugging, not as a stable machine API contract.

During development, inspect:

- number of cycles;
- model time;
- tool time;
- token use;
- repeated tool calls.

This catches cost/latency regressions before deployment.

## 5. Strands tracing is OpenTelemetry-based

Current Strands tracing uses OpenTelemetry.

That matters because you can integrate Agent traces into the observability ecosystem you already operate rather than inventing an Agent-specific tracing backend.

A trace can capture:

    Agent invocation
      ├── model call
      ├── tool execution
      ├── model call
      └── ...

For multi-agent systems, nested Agent/orchestrator spans let you see where work moved.

## 6. Smallest trace setup

**Code sample — verified**

~~~python
from strands import Agent
from strands.telemetry import StrandsTelemetry

StrandsTelemetry().setup_console_exporter()

agent = Agent()
agent("What is agent observability?")
~~~

The console exporter is a good local proof that spans are emitted.

Do not use console dumping as your production telemetry architecture.

## 7. Export traces with OTLP

Current StrandsTelemetry supports setup_otlp_exporter.

**Code sample — verified**

~~~python
from strands.telemetry import StrandsTelemetry

telemetry = StrandsTelemetry()
telemetry.setup_otlp_exporter()
~~~

The underlying OpenTelemetry SDK uses environment configuration such as:

- OTEL_EXPORTER_OTLP_ENDPOINT;
- OTEL_EXPORTER_OTLP_HEADERS;
- OTEL_SERVICE_NAME.

This lets you send traces through your collector/backend architecture.

Possible backends include OpenTelemetry-compatible systems such as AWS X-Ray through an appropriate OTel/ADOT path, Grafana Tempo, Jaeger, Datadog, and others.

Validate the exact exporter/backend configuration in your platform documentation.

## 8. Reuse an existing tracer provider when you already have one

Current StrandsTelemetry accepts a preconfigured tracer provider.

This matters in a real service where FastAPI, database clients, HTTP clients, and Strands should participate in one trace.

Do not accidentally create competing global tracer providers.

Use the current API reference to integrate with your organization's existing OpenTelemetry bootstrap.

## 9. Configure metrics export

Current StrandsTelemetry exposes setup_meter.

**Code sample — verified**

~~~python
from strands.telemetry import StrandsTelemetry

telemetry = StrandsTelemetry()

telemetry.setup_meter(
    enable_console_exporter=True,
    enable_otlp_exporter=True,
)
~~~

For production, you normally do not enable noisy console metrics unless your logging strategy intentionally wants them.

Use the OTLP path and your normal metrics backend.

## 10. Configure logging

Python Strands uses the standard logging hierarchy rooted under strands.

**Code sample — verified**

~~~python
import logging

logging.getLogger("strands").setLevel(logging.DEBUG)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
~~~

DEBUG is useful during development/troubleshooting.

In production, choose log levels intentionally.

Debug logging can expose operational details and may contain sensitive context depending on what your application/tools log.

## 11. Keep application logs structured

The SDK uses Python logging, so integrate it into your normal structured logging stack.

Useful fields:

    timestamp
    level
    service
    environment
    request_id
    session_hash
    agent_name
    model_id
    tool_name
    event
    duration_ms
    error_category

Do not build dashboards by regex-parsing long human sentences if you can emit stable fields.

## 12. Correlation ID should start at the request boundary

Generate or accept a validated request ID at the API/gateway layer.

Propagate it through:

    API
      → Agent invocation
      → tools
      → MCP
      → child Agents
      → A2A remote service
      → downstream APIs

This lets one incident be reconstructed across service boundaries.

A correlation ID is not authentication and should not contain sensitive user data.

## 13. Session IDs need special care

A raw session ID can become:

- sensitive;
- high-cardinality;
- tenant-identifying.

Avoid using raw user/session IDs as metric labels.

For traces/logs, use a safe internal correlation value or hash/pseudonymous representation consistent with your privacy policy.

## 14. Model identity should be observable

Record safe deployment dimensions such as:

- provider;
- model ID;
- Agent application version;
- prompt/policy version;
- environment.

Otherwise a model rollout regression appears as a mysterious behavioral change.

Keep these dimensions bounded; do not put arbitrary user text into labels.

## 15. Tool observability

For every tool, measure:

- call count;
- duration;
- success/failure;
- error category;
- retry count;
- result-size category;
- downstream service.

For high-impact tools also audit:

- operation type;
- approved resource;
- actor/policy decision;
- idempotency key;
- approval outcome.

Do not log secrets or raw PII merely for “debugging.”

## 16. MCP adds another observable hop

Agent trace:

    tool call = search_logs

MCP server:

    request received
      → downstream CloudWatch query
      → response

Correlate both sides.

If the Agent shows a 12-second tool span, server-side telemetry should tell you whether the time was:

- network;
- authentication;
- MCP queue;
- downstream service;
- response serialization.

## 17. A2A needs distributed tracing

For remote Agent calls:

    parent trace
      ↓ HTTP/A2A
    remote trace

Propagate trace context where your A2A/gateway instrumentation supports it.

At minimum carry a safe correlation ID.

Without propagation, multi-agent failures become separate disconnected logs.

## 18. Multi-agent cost attribution

For Agents-as-Tools:

    parent tokens
    + child tokens

For Graph:

    tokens per node

For Swarm:

    tokens per Agent
    + handoff count

Tag spans/results so you can identify which specialist is consuming budget.

A common optimization is deleting an Agent that adds little quality but large cost.

You cannot discover that without attribution.

## 19. Build operational SLOs

Do not use only CPU/memory.

Agent-facing SLOs include:

### Availability

Percentage of requests completing according to your API contract.

### Latency

- time to first approved streamed output;
- end-to-end completion p50/p95/p99.

### Quality proxy

- tool failure rate;
- escalation rate;
- budget-exhaustion rate;
- guardrail intervention rate;
- eval/online quality sample.

### Cost

- tokens/request;
- model cost/request;
- expensive tool calls/request.

Infrastructure health alone does not tell you whether an Agent is useful.

## 20. Alert on control failures

Useful alarms:

- sudden increase in limit_turns;
- token budget exhaustion spike;
- tool AccessDenied spike;
- remote A2A timeout spike;
- MCP connection errors;
- guardrail intervention anomaly;
- session-store failures;
- unusually high handoff counts;
- p95 model latency;
- total token surge.

Avoid alerting on every single model refusal or user mistake.

Alert on actionable system patterns.

## 21. PII and traces are a serious risk

A trace may include:

- prompt text;
- tool arguments;
- tool results;
- model output.

That can be more sensitive than normal web-service tracing.

Before exporting telemetry:

- define what content is captured;
- redact secrets;
- minimize PII;
- encrypt transport/storage;
- set retention;
- restrict access;
- review third-party backend data policy.

Do not assume “it is observability” makes data exempt from privacy rules.

## 22. Never put high-cardinality text into metrics labels

Bad label:

    prompt="Please analyze incident 123 ..."

This creates unbounded cardinality and leaks content.

Good bounded dimensions:

    environment=prod
    model=...
    agent=incident_commander
    tool=cloudwatch_query
    status=error

Use traces/logs for request-specific detail.

## 23. Sampling

At scale, tracing every full detail may be expensive.

A strategy can include:

- sample normal successful requests;
- keep all errors;
- keep all high-latency requests;
- keep all security/approval events;
- retain aggregate metrics at full coverage.

Sampling must not remove audit records that your security/compliance policy requires.

Audit logging and diagnostic tracing are related but not identical systems.

## 24. Debugging a slow request

Follow this sequence:

1. Find trace by request ID.
2. Inspect total duration.
3. Find longest child span.
4. If model:
   - provider latency?
   - retry/backoff?
   - large input tokens?
5. If tool:
   - downstream duration?
   - retry?
   - oversized result?
6. Check cycle count.
7. Check tokens.
8. Check context-management activity.
9. Compare with healthy baseline.

This is much faster than reading the final Agent answer.

## 25. Debugging a wrong answer

1. Find exact trace/trajectory.
2. Verify input and trusted policy version.
3. Inspect tool selected.
4. Inspect arguments.
5. Verify tool result.
6. Check whether tool result contained untrusted injection text.
7. Check context compression/summarization.
8. Check specialist routing.
9. Check final model synthesis.
10. Add a regression case to Lesson 16 dataset.

Every production failure should improve your future test set.

## 26. Dashboard design

A practical Agent dashboard can show:

### Overview

- request rate;
- success/incomplete/failure;
- p50/p95 latency;
- tokens/request;
- error rate.

### Model

- latency by model;
- throttling/retry;
- input/output tokens.

### Tools

- calls by tool;
- failure rate;
- p95 duration.

### Agent loop

- cycles/request;
- budget-limit rate.

### Multi-agent

- specialist invocations;
- Graph node failures;
- Swarm handoffs.

### Safety

- guardrail interventions;
- policy denials;
- approval-required actions.

Do not put sensitive prompt content on a shared dashboard.

## 27. CI/CD observability verification

A deployment pipeline should verify:

- telemetry initializes;
- service name/environment tags are correct;
- one synthetic Agent request emits expected trace;
- logs reach backend;
- metrics reach backend;
- alert/dashboard definitions deploy through IaC where practical.

Observability that is configured manually after launch will eventually drift.

## 28. Cost of observability

Telemetry itself costs:

- CPU;
- network;
- collector capacity;
- backend ingestion;
- retention.

Use sampling and data minimization.

Do not disable tracing entirely to save money; then the next Agent incident becomes far more expensive to diagnose.

## 29. Production checklist

- [ ] AgentResult metrics are reviewed during development.
- [ ] OpenTelemetry tracing is configured before Agent creation.
- [ ] OTLP exporter integrates with the platform backend.
- [ ] Metrics include latency, tokens, tools, and cycles.
- [ ] Structured logs use request correlation.
- [ ] Multi-agent work is attributable per specialist/node.
- [ ] MCP/A2A hops can be correlated.
- [ ] PII/secrets are excluded or redacted from telemetry.
- [ ] Metric labels are bounded-cardinality.
- [ ] SLO dashboards and actionable alarms exist.
- [ ] Telemetry deployment is part of IaC/CI/CD.

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/observability-evaluation/
- https://strandsagents.com/docs/user-guide/sdk/observability-evaluation/metrics/
- https://strandsagents.com/docs/user-guide/observability-evaluation/traces/
- https://strandsagents.com/docs/user-guide/sdk/observability-evaluation/logs/
- https://strandsagents.com/docs/api/python/strands.telemetry.config/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 18 — Security: Guardrails, PII Redaction & Responsible AI](18-security-guardrails-pii-redaction-responsible-ai.md). We will protect the model boundary, tool boundary, message-history boundary, identity boundary, and data boundary as separate controls.

Back to the [course README](../README.md).
