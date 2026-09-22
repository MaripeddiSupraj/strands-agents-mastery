# Lesson 12 — Multi-Agent Patterns: Agents as Tools

Strands Agents Mastery → Phase 4 — Multi-Agent Systems

The simplest useful multi-agent pattern in Strands is often not a Graph or a Swarm.

It is one orchestrator Agent with specialist Agents exposed as tools.

That gives you a familiar hub-and-spoke design:

    user
      ↓
    orchestrator
      ├── research specialist
      ├── security specialist
      └── operations specialist

The orchestrator decides which specialist to call. Each specialist can have its own prompt, model, and tools.

This pattern is a strong default when delegation is clear and you still want one Agent to own the user-facing conversation.

## Map of this lesson

- Why use an Agent as a tool
- The three current construction patterns
- Direct Agent tools
- as_tool customization
- Context reset and preserve_context
- Delegation
- Privilege isolation
- Failure handling
- Cost and latency
- Observability
- Evaluation
- When not to use this pattern

## 1. Why not one giant Agent?

You could build one Agent with:

- every tool;
- every instruction;
- every domain;
- every permission.

That quickly creates problems:

- too many tools for the model to choose from;
- larger prompt/context;
- broader privilege;
- harder evaluation;
- harder ownership;
- more accidental cross-domain behavior.

A specialist Agent gives you a smaller decision surface.

For example:

    incident commander
      ↓
    asks documentation specialist
      ↓
    documentation specialist has only read-only documentation tools

The specialist cannot restart production merely because the parent Agent can reason about remediation.

## 2. Direct Agent-as-tool pattern

Current Strands lets you pass another Agent directly in the tools list.

**Code sample — verified**

The structure below matches the current Agents-as-Tools documentation.

~~~python
from strands import Agent

research_agent = Agent(
    name="researcher",
    description="Researches factual questions and returns concise evidence.",
    system_prompt="You are a focused research specialist.",
)

orchestrator = Agent(
    system_prompt=(
        "You coordinate specialist agents. "
        "Use the researcher for factual research questions."
    ),
    tools=[research_agent],
)

result = orchestrator("Research the main differences between TCP and UDP.")
print(result)
~~~

The child Agent becomes a tool the parent model can select.

A clear name and description matter because they become part of the routing surface.

## 3. The orchestrator still runs an agent loop

The flow is roughly:

    user prompt
      ↓
    orchestrator model call
      ↓
    orchestrator requests researcher tool
      ↓
    child Agent runs its own loop
      ↓
    child result returns as tool result
      ↓
    orchestrator model sees result
      ↓
    orchestrator produces final answer

Notice the cost shape:

    parent model
      + child model
      + child tools
      + another parent model turn

Multi-agent composition increases model calls unless you deliberately use delegation, which we cover later.

## 4. Customize the specialist tool surface

Current Strands supports Agent.as_tool so you can give the tool-facing representation a clearer name and description.

**Code sample — verified**

~~~python
from strands import Agent

research_agent = Agent(
    name="researcher",
    description="General research specialist.",
)

orchestrator = Agent(
    system_prompt="Route factual research to the research assistant.",
    tools=[
        research_agent.as_tool(
            name="research_assistant",
            description=(
                "Process research questions that require factual information."
            ),
        ),
    ],
)
~~~

This is useful when the Agent's internal name is not the best description for parent routing.

## 5. By default, child context resets between calls

Current Strands documentation explicitly says that both direct Agent passing and as_tool reset the specialist Agent's conversation context between invocations by default.

That means:

    parent calls researcher(question A)
      ↓
    child runs
      ↓
    call completes
      ↓
    child conversation baseline resets

Then:

    parent calls researcher(question B)
      ↓
    fresh child conversation

This default reduces accidental context bleed between separate specialist calls.

It also makes each child call easier to reason about and evaluate.

## 6. Preserve specialist context only when you need it

Current Strands lets you preserve the child Agent's conversation across tool invocations.

**Code sample — verified**

~~~python
from strands import Agent

research_agent = Agent(
    name="researcher",
    description="Research specialist.",
)

orchestrator = Agent(
    system_prompt="Use the researcher for research work.",
    tools=[
        research_agent.as_tool(
            preserve_context=True,
        )
    ],
)
~~~

Use this only when the specialist genuinely needs continuity across multiple parent calls.

Tradeoffs:

- more token growth;
- more stale context;
- higher cross-task contamination risk;
- more difficult replay/evaluation.

For many enterprise tasks, the parent should pass the relevant context explicitly and let the child start clean.

## 7. Parent context and child context are different

Do not assume the child automatically receives every internal detail from the parent.

Think in terms of a tool boundary:

    parent decides what request to send
      ↓
    child receives that request
      ↓
    child reasons with its own prompt/tools/context
      ↓
    child returns result

This is healthy isolation.

Pass only the information the child needs.

Do not send the entire raw user/session history to every specialist by default.

## 8. Specialists should have focused tools

A research specialist might have:

- documentation MCP tools;
- read-only web/document retrieval.

A change specialist might have:

- change-ticket lookup;
- deployment action tools;
- approval hooks.

Do not give both Agents the union of all tools unless both truly require them.

Multi-agent architecture is useful partly because it can reduce privilege.

## 9. IAM should follow the specialist boundary

If specialists execute in the same Python process under one broad AWS role, their logical separation does not automatically create IAM separation.

For stronger isolation, you can deploy specialists separately or route privileged actions through a service/MCP boundary with a narrower identity.

Conceptually:

    orchestrator runtime role
      → invoke/read-only capabilities

    privileged operations service role
      → exact production action permissions

An Agent name is not an IAM principal.

The actual process/service identity controls AWS permission.

## 10. Custom Agent wrapper tool

Current Strands also documents wrapping an Agent manually with the tool decorator when you need custom pre-processing, post-processing, multiple parameters, or error handling.

**Code sample — illustrative**

The Agent and tool APIs are verified; the domain logic below is course-authored.

~~~python
from strands import Agent, tool

security_agent = Agent(
    system_prompt=(
        "You are a security review specialist. "
        "Return findings and evidence, not remediation commands."
    ),
)

@tool
def security_review(change_summary: str, environment: str) -> str:
    """Review a proposed change for security concerns."""
    if environment not in {"dev", "stage", "prod"}:
        return "Unsupported environment"

    response = security_agent(
        f"Environment: {environment}\n"
        f"Change summary: {change_summary}"
    )
    return str(response)
~~~

This wrapper gives deterministic application code a place to validate parameters before the child Agent runs.

## 11. Handle child failure as a tool failure

A child Agent can fail because of:

- model provider error;
- token/turn budget exhaustion;
- its own tool failure;
- guardrail intervention;
- timeout;
- cancellation.

Do not return a fabricated specialist answer when that happens.

A parent-facing tool should return or raise a clear bounded failure that the orchestrator can reason about.

For high-value workflows, include safe structured fields such as:

    specialist_status
    evidence_available
    retryable
    error_category

rather than dumping an exception trace into model context.

## 12. Give each child an invocation budget

A parent Agent budget does not remove the need to bound the child.

A specialist that loops internally can consume large cost before returning to the parent.

Use the same Lesson 03 discipline:

- turns;
- total tokens;
- output tokens;
- downstream tool timeouts;
- wall-clock deadlines.

When wrapping a child manually, you can call it with per-invocation limits.

**Code sample — illustrative**

~~~python
from strands import Agent, tool

research_agent = Agent(
    system_prompt="Return focused evidence only."
)

@tool
def bounded_research(query: str) -> str:
    """Research a bounded factual question."""
    result = research_agent(
        query,
        limits={
            "turns": 4,
            "output_tokens": 1500,
            "total_tokens": 6000,
        },
    )

    if result.stop_reason != "end_turn":
        return f"Research stopped: {result.stop_reason}"

    return str(result)
~~~

The limits syntax and stop_reason behavior are verified. The policy values are illustrative.

## 13. Delegation can remove an extra parent model round-trip

Current Strands supports delegated Agent tools through as_tool(delegate=True).

When a delegated specialist succeeds, its response can become the parent AgentResult directly instead of being returned to the orchestrator model for rewriting.

**Code sample — verified**

~~~python
from pydantic import BaseModel
from strands import Agent

class BillingResponse(BaseModel):
    summary: str
    refund_amount: float

billing_agent = Agent(
    name="billing_expert",
    description="Answers billing questions: charges, refunds, and invoices.",
    system_prompt="You handle billing questions with precision.",
    structured_output_model=BillingResponse,
)

orchestrator = Agent(
    system_prompt=(
        "Route billing questions to billing_expert. "
        "Answer general questions yourself."
    ),
    tools=[billing_agent.as_tool(delegate=True)],
)

result = orchestrator("Why was I charged twice?")
~~~

Why use delegation?

- preserve specialist-generated structured output;
- avoid unnecessary parent rephrasing;
- reduce one parent model round-trip;
- reduce tokens/latency.

## 14. Delegation has current limitations

At the time this lesson was verified, current Strands documentation calls out two important limitations:

1. A delegated tool must be the only tool selected in that parent turn. If the model requests it with other tools in the same batch, the batch is cancelled.
2. Delegation is not supported with stateful models that manage conversation state server-side because the early loop exit would leave the server-side function call incomplete.

Treat these as version-specific current behavior and check the live page when upgrading.

## 15. Do not blindly trust specialist output

A specialist is still an LLM-driven component.

Its result may be:

- incomplete;
- wrong;
- prompt-injected by its own tool data;
- policy-blocked;
- out of date.

For decisions that matter, keep provenance.

A useful specialist result can include:

    conclusion
    evidence
    source references
    uncertainty
    requested follow-up

Then the parent can reason about evidence rather than treating the child Agent as an oracle.

## 16. Security boundary around data sent to a specialist

Before invoking a child Agent, ask:

- Does it need the user's identity?
- Does it need raw PII?
- Does it use a different model/provider?
- Does it call an external MCP server?
- Is its trace exporter the same?
- Does it retain conversation?

Data minimization applies between Agents too.

If a specialist only needs a service name and error code, do not send the full customer ticket.

## 17. Model choice per specialist

One benefit of Agents-as-Tools is that each Agent can use a different model.

Examples:

- orchestrator: strong routing/reasoning model;
- simple classification specialist: smaller model;
- coding specialist: coding-optimized model;
- local sensitive-data specialist: approved local/provider model.

But every model split creates a new evaluation matrix.

Do not optimize cost before measuring specialist task quality.

## 18. Cost model

A typical non-delegated specialist call can look like:

    parent model call
      + child model call(s)
      + child tool call(s)
      + parent synthesis call

If the parent calls three specialists, cost can grow quickly.

Track:

- number of child calls;
- child turns;
- child tokens;
- parent turns;
- final synthesis tokens.

A multi-agent system should earn its extra cost through better task quality, isolation, or maintainability.

## 19. Latency and parallelism

An orchestrator model may decide to call multiple tools.

Whether child calls run in parallel depends on the tool/agent loop behavior and task shape.

Do not assume parallel execution will make a multi-agent system fast.

Measure:

- parent routing time;
- each child duration;
- slowest child;
- synthesis time.

If work has a deterministic parallel structure, Graph may be a clearer orchestration choice.

## 20. Observability

Tag traces with safe multi-agent dimensions:

- orchestrator Agent ID/name;
- specialist Agent ID/name;
- tool name;
- parent request ID;
- child duration;
- child stop reason;
- child token usage;
- delegation mode;
- error category.

You want to answer:

    Which specialist caused this request to become slow or expensive?

without opening raw prompts manually.

## 21. Evaluation should test routing and specialist quality separately

### Parent routing evaluation

Given input X:

- did the orchestrator select the right specialist?
- did it avoid unnecessary specialists?
- did it pass the right request?

### Child task evaluation

Given a specialist request:

- did the child use correct tools?
- did it produce correct evidence?
- did it stay within scope?
- did it stop safely on failure?

### End-to-end evaluation

- was the user's goal achieved?
- was cost acceptable?
- was sensitive data routed correctly?
- were unsafe actions avoided?

This layered approach tells you where a regression came from.

## 22. Failure exercise

Create two specialists:

- documentation_agent;
- operations_agent.

Make the operations specialist deliberately return a controlled failure.

Verify that the parent:

- does not invent an operation result;
- does not silently claim success;
- can still use documentation_agent if useful;
- reports that action evidence is unavailable.

This is more realistic than testing only successful delegation.

## 23. When Agents-as-Tools is the right pattern

Use it when:

- one Agent should own the conversation;
- delegation roles are clear;
- specialists can work largely independently;
- you want strong context/tool separation;
- the parent should synthesize the result.

It is especially good for:

    orchestrator
      → one or more domain specialists

## 24. When to choose Graph instead

Choose Graph when:

- the allowed path should be developer-defined;
- steps have dependencies;
- branches can run independently;
- you need explicit loops/review stages;
- execution order matters more than free-form routing.

Lesson 13 covers that.

## 25. When to choose Swarm instead

Choose Swarm when:

- the next specialist genuinely cannot be known ahead of time;
- agents should autonomously hand off;
- shared collaborative context is valuable;
- you accept higher emergent-path complexity.

Lesson 14 covers the additional safety controls required.

## 26. Production checklist

- [ ] Specialist names/descriptions clearly define routing.
- [ ] Each specialist has the minimum tool set.
- [ ] Runtime/IAM boundaries match real privilege requirements.
- [ ] Child Agents have independent execution budgets.
- [ ] Child failure becomes explicit tool failure.
- [ ] preserve_context is enabled only when justified.
- [ ] Sensitive data is minimized before specialist calls.
- [ ] Delegation limitations are understood.
- [ ] Parent routing and child behavior are evaluated separately.
- [ ] Traces identify parent/child cost and latency.

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/multi-agent/agents-as-tools/
- https://strandsagents.com/docs/user-guide/sdk/multi-agent/multi-agent-patterns/
- https://strandsagents.com/docs/user-guide/concepts/agents/agent-loop/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 13 — Multi-Agent Patterns: Graph Workflows](13-multi-agent-patterns-graph-workflows.md). We will replace free-form specialist routing with an explicit execution graph, including branching, cycles, limits, and per-node observability.

Back to the [course README](../README.md).
