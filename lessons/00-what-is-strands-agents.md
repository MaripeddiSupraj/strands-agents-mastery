# Lesson 00 — What Is Strands Agents?

Strands Agents Mastery → Phase 1 — Core Agent Mechanics

Before learning APIs, get the mental model right. Strands is not “a chatbot library with a few tools attached.” The Harness SDK gives you the execution machinery that repeatedly asks a model what to do, executes allowed tools, feeds results back, maintains conversation state, and exposes the lifecycle so you can control and observe it.

The current Strands project has two related entry points: the higher-level Strands harness with more defaults pre-wired, and the lower-level Harness SDK used throughout this course. We use the SDK because the goal is to understand and control the system, not hide it.

## Map of this lesson

- What an agent actually is
- What Strands provides
- What Strands deliberately does not provide
- The model–tool–loop mental model
- Python and TypeScript support
- Installation and first smoke test
- Production questions to ask before writing “agentic” code


## Recommended hands-on example — One tiny service-status Agent

> **Build today:** One Agent with one safe tool: `get_service_status(service)`.
>
> **Run:** `What is the status of payments-api?`
>
> **Observe:** the model can answer directly or request a registered tool; the application—not the prompt—decides what executable capability exists.
>
> **Why this example:** it gives you one simple mental model that the rest of the course will keep expanding.

Do not add memory, MCP, multiple Agents, or cloud deployment yet. The goal is to understand what makes an Agent different from one model call.


## 1. Start with the simplest definition

An agent is a program in which a model can decide the next action.

A normal LLM call looks roughly like this:

    input → model → output

A tool-using agent looks more like this:

    input
      ↓
    model decides
      ↓
    answer OR tool request
                 ↓
              tool runs
                 ↓
           tool result returns
                 ↓
              model decides again
                 ↓
               answer

That repeated decision/action cycle is the agent loop. Lesson 03 will take it apart in detail.

The important distinction is control flow. Your application no longer hard-codes every next function call. It gives the model a bounded set of possible actions, while the SDK keeps the loop running under rules you configure.

## 2. What Strands gives you

At the SDK level, Strands provides the core pieces needed to build this loop:

- Agent: the object you invoke.
- Model providers: Bedrock by default, plus supported external/local providers.
- Tools: Python/TypeScript functions, vended tools, MCP tools, or other agents.
- Agent loop: the machinery that sends messages to the model, executes requested tools, and continues.
- Conversation/context handling: how the growing interaction is presented to the model.
- Hooks/plugins: lifecycle extension points.
- Streaming/callbacks: incremental visibility into execution.
- Sessions: persistence across invocations.
- Multi-agent orchestration: agents-as-tools, Graph, Swarm, A2A, and workflow patterns.
- Telemetry and metrics: traces, token use, latency, and tool activity.
- Evaluation: a separate Strands Evals package for measuring behavior.

You should think of Strands as an agent harness: infrastructure around model calls that turns them into controlled, observable applications.

## 3. What Strands does not remove

Using an agent SDK does not remove normal software-engineering responsibilities.

You still own:

- authentication and authorization;
- IAM scope;
- secrets;
- the trust boundary around tools;
- network egress;
- data classification;
- PII handling;
- timeouts and budgets;
- retry policy;
- test coverage;
- model/provider selection;
- deployment architecture;
- incident response.

A useful enterprise rule is:

> The model may propose an action. Your application remains responsible for deciding which actions are possible and under what identity they execute.

If a tool can delete production data, the model effectively has access to that capability whenever the tool is available. “The prompt told it not to” is not an authorization control.

## 4. Current SDK shape

This course is Python-first because the Python SDK currently exposes the broadest feature surface. TypeScript is supported and is called out where its behavior materially differs.

The live Strands documentation changes quickly. In June 2026, the former standalone docs repository was archived and documentation/source moved into the Harness SDK monorepo. For that reason, this course does not freeze old code examples from memory.

The canonical places to check are:

- https://strandsagents.com/docs/
- https://github.com/strands-agents/harness-sdk
- https://github.com/strands-agents

## 5. Installation

**Code sample — verified**

The current Python quickstart requires Python 3.10 or newer and installs the SDK like this:

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install strands-agents
~~~

The community tools package is separate:

~~~bash
pip install strands-agents-tools
~~~

Do not install every optional provider dependency “just in case” in a production image. Smaller dependency sets reduce supply-chain surface and image size.

## 6. The smallest agent

Amazon Bedrock is the default provider in the current Python SDK.

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent()
print(agent("What can you help me build?"))
~~~

This tiny example hides several operations:

1. Agent receives your input.
2. It creates the model request from system/context/conversation state.
3. The model responds.
4. If the model requests a tool, the loop can execute it and continue.
5. Otherwise the loop ends and returns an AgentResult.

No tools means the model can only answer from the model-side capabilities and supplied context. Adding tools changes the security model because the agent can now cause external side effects.

## 7. Default Bedrock does not mean “no AWS setup”

The zero-argument Agent convenience is not zero infrastructure.

Your runtime still needs valid AWS credentials and permission to invoke the selected Bedrock model. Model availability and regional access also matter. In production, prefer workload identity such as an IAM role over static access keys.

A least-privilege direction is:

- permit only the Bedrock invoke actions you need;
- scope resources to the model/inference profile you actually call where IAM supports it;
- do not attach broad administrator policies to “make the demo work”;
- use separate roles for development, CI, and runtime.

Exact resource ARNs vary with model and Bedrock configuration, so validate them in the AWS service/IAM documentation for your deployment.

## 8. A tool changes the system

A tool is executable capability exposed to the model.

**Code sample — verified**

This pattern matches the current tools documentation:

~~~python
from strands import Agent, tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Weather lookup for {city} would happen here."

agent = Agent(tools=[get_weather])
agent("What is the weather in Pune?")
~~~

The decorator exposes a typed callable as an agent tool. In a real implementation, do not trust the city string merely because a model produced it. Validate arguments before crossing trust boundaries.

## 9. Why “agentic” is not automatically better

Use an agent when runtime reasoning about the next action provides real value.

Do not use an agent for a flow that should simply be:

    validate request → call API → return response

A deterministic function is cheaper, easier to test, and easier to audit.

Good agent candidates usually involve:

- ambiguous natural-language requests;
- multiple possible tools;
- planning/replanning;
- partial information;
- selecting which specialist should work next;
- iterative synthesis.

Even then, keep deterministic rules outside the model where possible.

## 10. The four boundaries to identify before coding

For every enterprise agent, write down four boundaries.

### 10.1 Data boundary

What information may enter model context?

Examples:

- public documentation: usually low sensitivity;
- customer tickets: may contain PII;
- credentials: should not enter model context;
- production logs: can contain secrets or customer data.

### 10.2 Action boundary

What may tools do?

Separate read actions from write actions. Separate reversible changes from destructive ones. High-impact writes should normally require stronger policy and often human approval.

### 10.3 Identity boundary

Under whose credentials do tools execute?

The safest model is not “the agent has admin.” Use workload identity, scoped service roles, short-lived credentials, and user-context authorization when the action is user-specific.

### 10.4 Budget boundary

How much can one request consume?

Bound:

- turns;
- tokens;
- retries;
- wall-clock time;
- expensive external API calls;
- multi-agent handoffs.

Strands exposes execution limits we will use in Lesson 03.

## 11. Observability starts now

Do not postpone observability until Lesson 17.

Even your first demo should answer:

- Which model handled the request?
- How many tokens did it use?
- Did it call a tool?
- How long did each step take?
- Why did the loop stop?
- Did a retry occur?

The SDK exposes AgentResult metrics and OpenTelemetry-based telemetry. We will progressively add these instead of treating observability as a late production add-on.

## 12. Testing starts before tools become dangerous

For the first agent, write tests around what you control rather than asserting exact model prose.

Useful early tests:

- tool argument validation;
- tool authorization;
- timeout behavior;
- stop/budget handling;
- output structure if you require structured output;
- known regression prompts.

Later we will add trajectory and behavior evaluation with Strands Evals.

## 13. Cost is architecture

Token cost is not just a billing detail. It changes architecture.

Long conversation history increases every later model request. Agentic retries add calls. Swarms multiply calls. Steering may add model work. Large tool output can inflate context.

Start with the cheapest model that meets the task’s reliability requirements, then measure. Do not choose a model only by benchmark reputation.

## 14. What you should be able to explain now

Before continuing, be able to answer:

1. Why is an agent different from one model call?
2. What does the SDK control versus what your application must control?
3. Why does adding a tool create a security boundary?
4. Why should an agent have a budget?
5. When would deterministic code be better than an agent?

If those answers are clear, the rest of the course has a stable foundation.

## Sources checked

Current sources used for this lesson:

- https://strandsagents.com/docs/user-guide/sdk/
- https://strandsagents.com/docs/user-guide/sdk/quickstart/python/
- https://strandsagents.com/docs/user-guide/sdk/quickstart/overview/
- https://strandsagents.com/docs/user-guide/sdk/tools/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 01 — Core Components Deep Dive](01-core-components-deep-dive.md), where we map every major SDK component before writing a larger application.

Back to the [course README](../README.md).
