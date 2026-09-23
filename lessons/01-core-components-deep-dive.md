# Lesson 01 — Core Components Deep Dive

Strands Agents Mastery → Phase 1 — Core Agent Mechanics

Lesson 00 gave us the mental model. Now we map the pieces. This lesson is deliberately broad: you should finish it knowing where a concern belongs before later lessons go deep on the API.

## Map of this lesson

- Agent
- Agent loop
- Models
- Tools
- Messages and context
- Sessions
- Hooks and plugins
- Streaming and callbacks
- Multi-agent orchestration
- Evaluation
- Observability
- Security
- Deployment


## Recommended hands-on example — Map every Strands component onto one future incident assistant

> **Scenario:** Eventually the course will build a payments-api incident assistant.
>
> While reading this lesson, map each component to that one system: **Agent** = incident commander, **model** = decision engine, **tools** = service/telemetry capabilities, **context** = current investigation evidence, **session** = incident continuity, **hooks** = deterministic policy, **specialist Agents** = domain workers, **telemetry** = how you explain cost/latency/failures.
>
> **Why this example:** Lesson 01 is intentionally broad. Using one future application stops the component map from feeling like a vocabulary list.

You are not expected to implement the whole system today. The implementation starts small in Lesson 02 and grows one capability at a time.


## 1. Agent: the application-facing entry point

The Agent object is the unit you normally invoke.

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent()
result = agent("Explain the agent loop in one sentence.")
~~~

The important architectural point is that Agent is not the model itself.

Think:

    Agent
      ├── model
      ├── tools
      ├── messages/context
      ├── hooks/plugins
      ├── session manager
      └── loop/control policy

That separation lets you switch providers, tools, persistence, and lifecycle behavior without rebuilding the entire application.

## 2. Agent loop: the engine

The loop repeatedly:

1. builds the model input;
2. calls the model;
3. interprets the response;
4. executes requested tools when allowed;
5. appends results;
6. repeats until a stop condition occurs.

This matters because every turn can add cost and latency.

A production agent needs a defined answer to:

> What prevents the loop from running longer than the business request deserves?

Current Strands supports per-invocation limits such as turns and tokens. We use them in Lesson 03.

## 3. Models: decision engines behind a common harness

Strands supports multiple model providers. Amazon Bedrock is the default in the Python quickstart; documented providers also include Anthropic, OpenAI, Google, Ollama and others.

The provider abstraction matters because the rest of your agent can remain largely stable while you change the model object.

Do not confuse API compatibility with behavioral equivalence. Two providers can both support tool calling yet differ in:

- tool-selection quality;
- latency;
- context window;
- structured-output reliability;
- prompt caching;
- throughput limits;
- price;
- regional/compliance posture.

Provider switching therefore requires evaluation, not only a successful import.

## 4. Tools: capabilities, not “plugins”

A tool is a callable capability the model may request.

Strands supports several tool sources:

- custom functions;
- vended tools;
- community tools;
- MCP tools;
- other Agents exposed as tools.

**Code sample — verified**

~~~python
from strands import Agent, tool

@tool
def lookup_order(order_id: str) -> str:
    """Look up an order by ID."""
    return f"order={order_id}"

agent = Agent(tools=[lookup_order])
~~~

For production, split tools by privilege. A read-only order lookup and a refund tool should not be treated as equally safe just because both use the same decorator.

## 5. Tool descriptions are part of control quality

The model chooses tools based partly on tool names, descriptions, schemas, and current context.

A vague description increases accidental calls.

Bad:

    "Does stuff with orders"

Better:

    "Read order status by order ID. This tool never changes an order."

Good tool metadata helps selection, but it is still not authorization. Enforce permission in code.

## 6. Messages and conversation history

Agent interactions become message history that later model calls can see.

That gives continuity, but it creates three production pressures:

1. Context grows.
2. Earlier untrusted content may keep influencing later calls.
3. Retaining conversation may become a privacy/compliance decision.

Context management and session persistence solve different problems:

- context management controls what fits/is useful in the model’s working context;
- session management persists state across invocations/processes.

We treat them separately in Lessons 10 and 11.

## 7. Context management

Current Strands exposes first-class context management. The documented convenience mode is:

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent(context_manager="auto")
~~~

The goal is not merely “truncate old text.” A context strategy should preserve information needed to finish the task while controlling context-window pressure and token cost.

The current SDK also exposes an agentic mode and custom strategies. We will not guess custom APIs here; Lesson 10 uses only syntax verified from the current reference.

## 8. Sessions: durable continuity

A session manager persists state so an agent can resume after another invocation or process lifecycle.

For new single-agent Python workloads, the current documentation recommends SnapshotSessionManager.

**Code sample — verified**

~~~python
from strands import Agent
from strands.session import SnapshotSessionManager
from strands.storage import LocalFileStorage

session_manager = SnapshotSessionManager(
    session_id="demo-session",
    storage=LocalFileStorage("./sessions/"),
)

agent = Agent(session_manager=session_manager)
~~~

Local filesystem persistence is useful for learning, not automatically appropriate for horizontally scaled production.

For Graph/Swarm, SnapshotSessionManager is not the correct manager; use a repository-based session manager on the orchestrator, and do not attach independent session managers to child agents.

## 9. Hooks: lifecycle control points

Hooks let application code react at defined lifecycle points such as invocation, model call, or tool call.

Use hooks for cross-cutting behavior:

- approval gates;
- logging;
- policy enforcement;
- input/output checks;
- retry control;
- instrumentation.

**Code sample — verified**

~~~python
from strands import Agent
from strands.hooks import BeforeInvocationEvent

agent = Agent()

def before_invocation(event: BeforeInvocationEvent) -> None:
    print("Invocation is starting")

agent.add_hook(before_invocation)
~~~

A hook is more reliable than repeatedly telling the model “remember to log every action” because it is application control flow.

## 10. Plugins: reusable behavior packages

Plugins package reusable Agent behavior using SDK extension points such as hooks.

Current built-in/plugin surfaces include Skills and Steering-related integrations. Plugins can change behavior significantly, so treat third-party plugins like executable dependencies, not prompt templates.

Review:

- code origin;
- permissions;
- network access;
- hook points;
- data captured;
- version pinning.

## 11. Streaming and callbacks

Streaming is not the same as “faster inference.” It exposes partial progress earlier.

Current Python supports async streaming through Agent.stream_async.

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent(callback_handler=None)

async def run():
    async for event in agent.stream_async("Explain DNS simply."):
        if "data" in event:
            print(event["data"], end="", flush=True)
~~~

Streaming is especially useful for user-facing applications and long tool workflows, but do not leak internal sensitive tool data merely because it appears in an event stream.

Python also exposes callback handling. TypeScript primarily uses async iteration and hooks for this style of control.

## 12. Multi-agent patterns

Strands currently documents several ways to compose agents.

### Agents as tools

Hub-and-spoke delegation. An orchestrator selects specialist agents as tools.

Good when the delegation structure is clear.

### Graph

Developer-defined nodes and edges with deterministic structure and support for branching/cycles.

Good when you can draw the allowed workflow.

### Swarm

A pool of specialist agents that autonomously hand off work.

Good for open-ended collaboration where the path is not known in advance.

### A2A

Agent-to-Agent protocol support for communicating with remote agents.

Good when agents are deployed independently or built by different systems.

A common mistake is choosing Swarm because it sounds sophisticated. Use the simplest coordination pattern that meets the problem.

## 13. Evaluation

Testing an agent has two layers.

### Deterministic software tests

Test:

- schemas;
- validation;
- authorization;
- parsing;
- retry/timeout code;
- deterministic routing logic.

### Behavioral evaluation

Measure:

- output quality;
- tool-selection accuracy;
- parameter accuracy;
- instruction following;
- goal success;
- failure communication;
- recovery behavior.

The current Strands Evals SDK provides built-in evaluator families for these concerns. Lesson 16 builds an evaluation gate suitable for CI.

## 14. Observability

Strands is OpenTelemetry-oriented and also exposes execution metrics on AgentResult.

You should be able to correlate:

    request
      → model call
      → tool call
      → model call
      → final result

with token and latency data.

**Code sample — verified**

~~~python
from strands.telemetry import StrandsTelemetry

StrandsTelemetry().setup_console_exporter()
~~~

This is useful locally. In production, export through your approved OpenTelemetry path/backend and apply data-redaction policy before traces leave the workload.

## 15. Security model

The most important security fact in the SDK is simple:

> Tools execute with the permissions of the process/environment in which they run.

That means your effective agent permissions are determined by executable tools plus runtime identity.

Guardrails can filter model input/output. They do not replace tool authorization.

Security layers should include:

- validated input;
- minimal tool set;
- argument validation;
- resource-level authorization;
- least-privilege runtime identity;
- guardrails/data controls;
- approval for high-impact changes;
- audit logging;
- bounded execution.

## 16. Deployment targets

Current Strands documentation covers several deployment targets including:

- Amazon Bedrock AgentCore;
- AWS Lambda;
- Amazon ECS/Fargate;
- Amazon EKS;
- App Runner;
- EC2;
- Docker/Kubernetes.

The SDK does not make every target equally suitable.

For example:

- short request/response workloads can fit Lambda;
- streaming or long-lived container workloads often fit Fargate/EKS better;
- AgentCore Runtime is purpose-built for agent workloads and is the capstone target in this course.

Lesson 19 compares the operational tradeoffs rather than treating deployment as one generic Docker step.

## 17. A component-to-risk map

| Component | Main engineering question |
| --- | --- |
| Agent | What behavior is this object allowed to own? |
| Model | What capability, cost, region, and data policy apply? |
| Tool | What side effect and privilege does it expose? |
| Context | What should the model see right now? |
| Session | What should survive across invocations? |
| Hook | What must happen deterministically around lifecycle events? |
| Plugin | What reusable behavior/code are we trusting? |
| Streaming | What partial data can clients safely observe? |
| Multi-agent | Why is another agent needed, and how is fan-out bounded? |
| Evaluation | How do we know a change is actually better? |
| Telemetry | Can we explain latency, cost, and failures? |
| Deployment | What identity, network, scaling, and recovery model applies? |

Keep this table in mind for the rest of the course.


## 18. Current Strands Harness: the batteries-included path

The live Strands documentation now has two related layers:

- **Strands Harness SDK** — the lower-level SDK this course teaches so you understand the loop, tools, state, sessions, policy, and orchestration.
- **Strands harness** — a separately installed, fully assembled harness with tuned defaults for tools, context management, sessions, memory, and hooks.

**Code sample — verified**

~~~bash
pip install strands-harness
~~~

~~~python
from strands_harness import create_harness

agent = create_harness()
agent("Investigate the payments-api incident and write a concise summary.")
~~~

The current documentation states that `create_harness()` returns a standard Strands `Agent`, not an unrelated wrapper.

Use the assembled Harness when its defaults fit. Use the lower-level SDK when you need explicit architecture/control. Knowing both prevents a convenience API from becoming hidden magic.

Runnable lab: [harness_quickstart.py](../examples/01-core-components-deep-dive/harness_quickstart.py).

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/
- https://strandsagents.com/docs/user-guide/sdk/tools/
- https://strandsagents.com/docs/user-guide/concepts/agents/session-management/
- https://strandsagents.com/docs/user-guide/concepts/agents/context-management/
- https://strandsagents.com/docs/user-guide/concepts/hooks/
- https://strandsagents.com/docs/user-guide/sdk/multi-agent/multi-agent-patterns/
- https://strandsagents.com/docs/user-guide/observability-evaluation/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 02 — Your First Agent, Hands-On](02-your-first-agent-hands-on.md). We will create a small agent, inspect its result, add one safe tool, and debug the common first-run failures.

Back to the [course README](../README.md).
