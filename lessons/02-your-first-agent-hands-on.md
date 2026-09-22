# Lesson 02 — Your First Agent, Hands-On

Strands Agents Mastery → Phase 1 — Core Agent Mechanics

This lesson turns the component map into something you can run. Keep the first application deliberately small. The goal is to observe the harness, not hide mistakes inside a large project.

## Map of this lesson

- Create an isolated Python environment
- Run a model-only Agent
- Add one custom tool
- Inspect metrics
- Add simple validation
- Diagnose common failures
- Define a small test boundary

## 1. Prerequisites

Current Python quickstart requirements:

- Python 3.10+
- a virtual environment
- a configured model provider

This course starts with the default Amazon Bedrock path, then Lesson 04 shows provider switching.

For AWS production workloads, prefer an IAM role or workload identity. Avoid copying long-lived access keys into source code or container images.

## 2. Create the project

**Code sample — verified**

~~~bash
mkdir strands-first-agent
cd strands-first-agent

python -m venv .venv
source .venv/bin/activate

pip install strands-agents
~~~

Create agent.py.

## 3. Run the smallest possible Agent

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent()
result = agent("What is an agent harness, in one sentence?")

print(result)
~~~

Run it:

**Code sample — verified**

~~~bash
python -u agent.py
~~~

If this works, prove the environment before adding tools.

Do not immediately add memory, MCP, plugins, and a web server. When five components are introduced at once, a credential failure and a tool-schema failure become harder to separate.

## 4. What happened?

The rough path was:

    your prompt
      ↓
    Agent
      ↓
    Bedrock model request
      ↓
    model response
      ↓
    AgentResult

With no tools exposed, the loop did not need an action cycle.

Later a tool call changes the path:

    prompt
      ↓
    model
      ↓
    tool request
      ↓
    your function executes
      ↓
    result is appended
      ↓
    model sees result
      ↓
    final answer

That second model call is one reason tool use can increase token and latency cost.

## 5. Add one custom tool

Use a deterministic example rather than a tool that touches production.

**Code sample — verified**

The custom-tool shape matches current Strands tool documentation.

~~~python
from strands import Agent, tool

@tool
def get_service_status(service: str) -> str:
    """Return the demo health status for an approved service name."""
    statuses = {
        "payments-api": "healthy",
        "orders-api": "degraded",
    }

    normalized = service.strip().lower()
    if normalized not in statuses:
        return "unknown service"

    return statuses[normalized]

agent = Agent(tools=[get_service_status])

result = agent(
    "Check the orders-api status. If it is degraded, explain the situation "
    "without inventing a root cause."
)

print(result)
~~~

The model decides whether to call get_service_status. Your function still decides what inputs it accepts and what data it returns.

## 6. Why the validation belongs inside the tool

Suppose your prompt says:

    Only use approved service names.

That is useful guidance, but it is not validation.

The function itself normalizes and restricts names. In a production tool, validation should be even more explicit:

- schema/type constraints;
- length limits;
- allowlists where appropriate;
- tenant/resource authorization;
- safe encoding;
- downstream timeout;
- explicit error mapping.

Do not pass model-generated strings directly into shells, SQL, filesystem paths, cloud APIs, or infrastructure commands.

## 7. Inspect the loaded tools

**Code sample — verified**

Current Python documentation exposes these inspection surfaces:

~~~python
print(agent.tool_names)
print(agent.tool_registry.get_all_tools_config())
~~~

This is useful during testing and startup validation.

In production, be careful about returning a full tool registry to an end user; descriptions and schemas can reveal internal capabilities.

## 8. Look at execution metrics

**Code sample — verified**

The current metrics documentation exposes accumulated token usage, cycle durations, and tool metrics on AgentResult:

~~~python
result = agent("What is the status of orders-api?")

print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
print(f"Tools used: {list(result.metrics.tool_metrics.keys())}")
~~~

Do this while developing. It makes the cost/latency effect of each feature visible.

Metrics fields may expand over SDK versions, so build dashboards defensively rather than assuming every provider emits every optional field.

## 9. Common first-run error: credentials

Symptom: authentication/authorization errors before the model can respond.

Check in this order:

1. Does the runtime have AWS credentials?
2. Are you in the intended AWS account?
3. Is the configured region correct?
4. Is model access available there?
5. Does the runtime role have the required Bedrock invoke permission?

Do not “fix” this by attaching AdministratorAccess.

Use CloudTrail/IAM tooling to identify the exact denied action, then grant the smallest permission required.

## 10. Common first-run error: model/region mismatch

A model identifier or inference profile available in one region may not be available in another.

Do not hard-code a model assumption into dozens of source files. Centralize model configuration and validate it at startup.

A good production configuration records:

- provider;
- model ID;
- region;
- inference profile if applicable;
- max output tokens;
- temperature/other generation settings;
- service tier if used.

Lesson 04 makes this explicit.

## 11. Common first-run error: tool never called

Possible reasons:

- tool description is unclear;
- user request does not require the tool;
- another tool looks more relevant;
- the model/provider handles tool calling differently;
- the tool schema is confusing.

Do not force a tool by adding increasingly aggressive prompt text before checking its description and schema.

A tool should say what it does and, where helpful, what it does not do.

## 12. Common first-run error: tool called with bad arguments

Treat arguments as untrusted.

For an AWS-resource tool, validate:

- account/tenant scope;
- region;
- resource identifier format;
- allowed operation;
- request size;
- caller authorization.

Then handle downstream failures explicitly. “Tool execution failed” is not enough operational context for an on-call engineer.

## 13. Common first-run error: too much output

A tool that dumps 20 MB of logs into context can create:

- context-window pressure;
- token cost;
- latency;
- accidental secret/PII exposure.

Prefer bounded, filtered results. For observability queries, return the minimum evidence the agent needs and store large raw artifacts outside model context.

Lesson 10 shows context-management strategies; Lesson 18 covers data boundaries.

## 14. Add basic logging during development

**Code sample — verified**

Current Strands logging uses Python logging under the strands logger:

~~~python
import logging

logging.getLogger("strands").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
~~~

Do not leave DEBUG logging enabled blindly in production. Debug output can expose prompts, tool data, identifiers, or secrets depending on your application.

## 15. A small deterministic unit test

The model output is nondeterministic. Your tool validation is not.

**Code sample — illustrative**

~~~python
def test_unknown_service_is_rejected():
    # Test the pure business logic behind the tool in your own module.
    statuses = {
        "payments-api": "healthy",
        "orders-api": "degraded",
    }

    assert statuses.get("secret-admin-api", "unknown service") == "unknown service"
~~~

In a real repository, keep business logic separate from the decorated tool adapter so it is easy to unit-test without invoking a model.

## 16. A behavioral test idea

You also need a higher-level test such as:

    Given: "What is the status of orders-api?"
    Expect:
      - the status tool is called;
      - argument is orders-api;
      - final answer states degraded;
      - final answer does not invent a root cause.

Do not implement this by exact-string matching the final prose. Lesson 16 will use tool/trajectory evaluators designed for agent behavior.

## 17. First production checklist

Before you expose even this tiny agent through an API:

- [ ] runtime identity is least privilege;
- [ ] no static secrets in source;
- [ ] tool inputs are validated;
- [ ] tool output is bounded;
- [ ] model/provider config is centralized;
- [ ] request timeout is defined;
- [ ] invocation budget is defined;
- [ ] logs do not intentionally contain secrets;
- [ ] token/latency metrics are captured;
- [ ] deterministic tool tests exist;
- [ ] at least one behavioral regression case exists.

The next lesson gives you the missing piece: hard bounds around the loop itself.

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/quickstart/python/
- https://strandsagents.com/docs/user-guide/sdk/tools/
- https://strandsagents.com/docs/user-guide/sdk/tools/using-tools/
- https://strandsagents.com/docs/user-guide/observability-evaluation/metrics/
- https://strandsagents.com/docs/user-guide/observability-evaluation/logging/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 03 — How Agents Really Work](03-how-agents-really-work.md). We will trace the full loop, stop reasons, budgets, cancellation, concurrency, retries, and telemetry.

Back to the [course README](../README.md).
