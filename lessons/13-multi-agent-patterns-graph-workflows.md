# Lesson 13 — Multi-Agent Patterns: Graph Workflows

Strands Agents Mastery → Phase 4 — Multi-Agent Systems

A Graph is the right multi-agent pattern when the allowed execution structure matters.

Instead of asking one orchestrator model to decide everything, you define nodes and edges:

    research
       ├── analysis
       └── fact check
             ↓
          report

The agents still reason inside their nodes. The application controls which paths exist.

That gives you a useful balance:

    model intelligence inside nodes
    + deterministic orchestration structure between nodes

## Map of this lesson

- Graph mental model
- GraphBuilder
- Nodes and edges
- Parallel branches
- Conditional edges
- Cycles and review loops
- Hard safety limits
- reset_on_revisit
- Timeouts
- Node privilege
- Session persistence
- Streaming and observability
- Testing graphs
- Graph versus Workflow, Agents-as-Tools, and Swarm


## Recommended hands-on example — Make the incident investigation path explicit

> **Build today:** Express a payments-api investigation as a Graph where the application controls the allowed path:
>
> `collect evidence → analyze evidence → independently check AWS docs → produce incident report`
>
> Add a review/revisit path only when the analysis says evidence is insufficient.
>
> **Run:** `Investigate INC-2841 and produce an evidence-backed incident summary.`
>
> **Observe:** node order, parallel/conditional paths where used, revisit count, timeout/iteration bounds, and the output contributed by each node.
>
> **Why this example:** the learner can compare it directly with Lesson 12. Agents-as-Tools lets the commander choose delegation dynamically; Graph makes the allowed workflow itself explicit.

Use the verified `GraphBuilder` syntax later in this lesson. The block above is the recommended scenario, not a substitute API.


## 1. Why Graph exists

Imagine a report pipeline:

1. research;
2. independently analyze;
3. independently fact-check;
4. write report only after both are done.

That dependency structure is known before runtime.

A Swarm would add unnecessary routing freedom.

Agents-as-Tools could work, but then a parent model must repeatedly choose the sequence.

Graph lets the developer encode the dependency structure directly.

## 2. Current GraphBuilder

Current Python Strands exposes GraphBuilder from strands.multiagent.

The current component documentation lists core builder operations including:

- add_node;
- add_edge;
- set_entry_point;
- set_max_node_executions;
- set_execution_timeout;
- set_node_timeout;
- reset_on_revisit;
- build.

These are the control points we use in this lesson.

## 3. Build a basic graph

**Code sample — verified**

The following structure directly matches the current Strands Graph documentation.

~~~python
from strands import Agent
from strands.multiagent import GraphBuilder

researcher = Agent(
    name="researcher",
    system_prompt="Research the topic and return evidence.",
)

analyst = Agent(
    name="analyst",
    system_prompt="Analyze the research and identify implications.",
)

fact_checker = Agent(
    name="fact_checker",
    system_prompt="Verify claims and flag unsupported statements.",
)

report_writer = Agent(
    name="report_writer",
    system_prompt="Write the final report from validated inputs.",
)

builder = GraphBuilder()

builder.add_node(researcher, "research")
builder.add_node(analyst, "analysis")
builder.add_node(fact_checker, "fact_check")
builder.add_node(report_writer, "report")

builder.add_edge("research", "analysis")
builder.add_edge("research", "fact_check")
builder.add_edge("analysis", "report")
builder.add_edge("fact_check", "report")

builder.set_entry_point("research")
builder.set_execution_timeout(600)

graph = builder.build()

result = graph(
    "Research the impact of AI on healthcare and create a report."
)
~~~

The key is not the topic. It is the structure.

## 4. Think in dependencies

The graph above says:

    research must finish first

Then:

    analysis and fact_check depend on research

Finally:

    report depends on both upstream paths

This makes the orchestration easier to review than a prompt saying:

    “Please remember to do research, then analysis and fact checking,
    and only then write the report.”

Control flow belongs in code when it is known.

## 5. A node can be more than a simple Agent

Current Graph components support nodes wrapping AgentBase and MultiAgentBase implementations. Current Python Graph support also includes A2AAgent in supported Graph scenarios.

That means a node can represent:

- a normal local Agent;
- another Graph/Swarm where supported;
- a remote A2A Agent in current Python Graph support.

Nested orchestration can become expensive and difficult to debug, so use it only when the boundary adds real value.

## 6. Parallel branches can reduce latency

If analysis and fact checking are independent after research, they can be candidates for concurrent execution within the Graph engine.

Parallelism helps when:

- there is no data dependency between branches;
- downstream systems can handle concurrency;
- provider/tool quotas allow it.

Parallelism does not reduce total model cost.

It can also increase peak rate and trigger throttling.

Watch:

- model request rate;
- MCP/API limits;
- database concurrency;
- AWS service quotas.

## 7. Do not create fake parallelism

If node B needs the output of node A, connect the dependency.

Do not run both in parallel and ask B to “figure it out later.”

Graph structure should reflect real information dependencies.

That makes failures and retries easier to reason about.

## 8. Conditional edges

Current Python Graph supports conditional edges.

A condition examines Graph execution state and decides whether an edge should be traversed.

The official docs show patterns such as:

    reviewer
      ├── approved → publisher
      └── revision needed → draft writer

For exact GraphState/result access in your pinned SDK, copy the current Graph conditional-edge example rather than guessing field names.

The verified builder shape is:

**Code sample — verified**

~~~python
builder.add_edge(
    "reviewer",
    "publisher",
    condition=is_approved,
)
~~~

The condition function itself is application code and should be deterministic where possible.

## 9. Prefer deterministic routing conditions when the condition is deterministic

If approval is a structured field:

    status = "approved"

then route on that field.

Do not ask another model:

    “Does this look approved?”

unless the approval decision genuinely requires model judgment.

Structured node outputs make conditional routing safer.

## 10. Cycles enable review/revision loops

Graph can represent a cycle:

    draft
      ↓
    review
      ├── approved → publish
      └── changes needed → draft

This is useful for:

- code review;
- document quality;
- fact correction;
- planning/replanning.

It is also a direct path to an infinite loop if you do not set limits.

## 11. Bound cyclic graphs

Current Strands GraphBuilder supports total node-execution and wall-clock limits.

**Code sample — verified**

~~~python
builder.set_max_node_executions(10)
builder.set_execution_timeout(300)
builder.reset_on_revisit(True)

graph = builder.build()
~~~

For any cycle, set a finite node-execution limit.

A review loop that never converges should terminate as a bounded failure, not consume unlimited model calls.

## 12. reset_on_revisit

Current GraphBuilder exposes reset_on_revisit to control node state when a node is visited again.

Why this matters:

- a reviewer sends a draft back;
- the draft writer runs again;
- should its prior execution state be reused or reset?

State reuse can preserve useful context.

It can also accumulate stale assumptions.

Choose intentionally and test both the correctness and token impact.

## 13. Set node timeouts as well as graph timeout

A total Graph timeout bounds the whole orchestration.

An individual node timeout prevents one slow node from consuming the entire budget.

Current GraphBuilder exposes set_node_timeout.

Use:

    graph deadline
      +
    per-node deadline
      +
    downstream tool/network timeout

The exact timeout values should reflect your SLO and node role.

Do not set every layer to the same number without understanding which one fires first.

## 14. One failing node should not become fake downstream success

If fact_check fails, report_writer should not silently receive “nothing” and produce a fully confident report.

Define failure policy:

- fail the Graph;
- route to a recovery node;
- mark output partial;
- ask for human review.

The policy should be visible in Graph structure/application code.

## 15. Least privilege per node

A Graph is a good place to separate capability.

Example:

    research node
      → read-only MCP/documentation

    analysis node
      → no external tools

    deployment node
      → narrow deployment action
      → approval hook
      → privileged service identity

Do not give every node every tool “for convenience.”

If nodes run in the same process, IAM is still shared at process level unless external services/remote Agents create stronger boundaries.

Use separate deployed A2A services when you need independent runtime identity.

## 16. Graph state is not automatically trusted

Nodes can consume results from earlier nodes.

An upstream Agent result may contain:

- mistakes;
- untrusted retrieved text;
- prompt injection;
- PII.

Downstream Agents should know which content is:

- trusted application metadata;
- model output;
- external evidence;
- user input.

A graph edge transports data; it does not certify it.

## 17. Limit what crosses each node boundary

A common anti-pattern:

    each node receives the full history of everything

Better:

- pass the specific upstream result required;
- preserve evidence references;
- keep large artifacts in storage;
- retrieve details on demand;
- redact sensitive fields.

This controls context size and reduces accidental instruction bleed.

## 18. Session persistence: use the conservative current Python path

As noted in Lesson 11, current Strands session documentation is moving quickly.

The current user guide explicitly advises Python Graph/Swarm users to use a repository-based session manager on the orchestrator and not attach independent session managers to child Agents.

Until the user guide and latest SnapshotSessionManager API wording are fully reconciled for your pinned release, use that conservative pattern for production Graphs.

A conceptual Python setup is:

**Code sample — verified**

~~~python
from strands.session import FileSessionManager

session_manager = FileSessionManager(
    session_id="graph-session",
)
~~~

Attach the session manager according to the current Graph constructor/API for your pinned SDK. Do not guess constructor syntax if your version differs.

For distributed production, use the supported durable repository storage path rather than local files.

## 19. Session identity still needs authorization

A persisted Graph session may contain outputs from multiple specialists.

Treat the session as sensitive application data.

Authenticate/authorize the caller before resuming it.

Do not let the client-supplied session ID alone choose which orchestration state is loaded.

## 20. Stream Graph execution

Current Graph supports asynchronous streaming.

The current documentation exposes multi-agent events such as node-start events during graph streaming.

For the exact event dictionary fields in your pinned version, use the current streaming reference.

The safe public UX should expose coarse states such as:

    research started
    research complete
    analysis started
    fact check started
    report generation started
    request complete

Do not dump raw node prompts/results to a browser.

## 21. Observe each node separately

A useful trace hierarchy is:

    request
      ↓
    graph
      ├── research node
      │     ├── model
      │     └── MCP tool
      ├── analysis node
      │     └── model
      ├── fact-check node
      │     └── model
      └── report node
            └── model

Track:

- node status;
- node duration;
- node tokens;
- tool duration;
- branch concurrency;
- graph total duration;
- total node executions;
- stop/failure reason.

Otherwise a 90-second graph becomes one opaque trace span.

## 22. Cost grows with fan-out

If research fans out to five specialist nodes, you may create five model calls in parallel.

Parallel means faster wall clock, not cheaper.

A Graph cost budget should include:

    max node executions
    × expected tokens per node
    + tool/API cost
    + retries

Use evaluation to prove each branch contributes useful quality.

Delete “nice to have” Agents that do not improve measurable results.

## 23. Test node logic independently

Each Agent node should have its own tests/evals.

Then test the Graph.

### Unit tests

- condition functions;
- routing predicates;
- data normalization;
- failure mapping.

### Node evals

- specialist task quality;
- tool use;
- safety.

### Graph integration tests

- correct branch execution;
- convergence of cycles;
- failure propagation;
- timeout behavior;
- no execution of unreachable nodes.

### End-to-end evals

- business goal;
- total cost;
- latency;
- policy.

## 24. Test the cycle that does not converge

This is mandatory for a cyclic graph.

Construct an input where the reviewer keeps requesting changes.

Verify:

- max node execution limit stops the graph;
- output is marked incomplete/failed;
- no publication/action node runs;
- trace explains where the loop spent time.

A safety limit that has never been exercised is not proven.

## 25. Graph versus Workflow

Current Strands multi-agent docs distinguish Graph from Workflow.

Graph:

- flexible flow;
- branching;
- cycles;
- LLM-capable nodes;
- useful when routing can be dynamic.

Workflow:

- fixed task DAG;
- no cycles;
- deterministic dependency execution;
- good when the task graph itself is fixed.

This course focuses on Graph because the roadmap explicitly teaches it, but do not choose Graph for a static pipeline that is clearer as a Workflow.

## 26. Graph versus Agents-as-Tools

Agents-as-Tools:

    one parent Agent chooses specialists

Graph:

    developer defines allowed inter-node path

Use Graph when the structure itself is part of your control policy.

## 27. Graph versus Swarm

Graph:

    paths explicitly defined

Swarm:

    agents autonomously hand off

If you can draw the correct allowed flow, Graph is usually easier to operate and audit.

Use Swarm only when emergent routing has real value.

## 28. CI/CD for graph changes

Treat edge/node changes like control-flow changes.

A pull request should show:

- node added/removed;
- edge added/removed;
- condition changed;
- privilege/tool change;
- execution-limit change;
- expected cost impact;
- eval results.

A new edge to a privileged node deserves security review.

## 29. Production checklist

- [ ] Graph encodes real dependencies.
- [ ] Cycles have finite max node executions.
- [ ] Graph and node timeouts are defined.
- [ ] Failure propagation is explicit.
- [ ] Conditions are deterministic where possible.
- [ ] Privileged tools are isolated to required nodes.
- [ ] Cross-node data is minimized and provenance-preserving.
- [ ] Python session persistence follows the current supported orchestrator pattern.
- [ ] Each node is observable independently.
- [ ] Cyclic non-convergence is tested.
- [ ] Cost impact of fan-out is measured.


## 28. Workflow is a distinct multi-agent pattern

Current Strands documents **Workflow** separately from Graph.

Use Workflow when execution is a fixed task sequence/DAG with explicit dependencies.

| Pattern | Who decides the next path? | Best fit |
| --- | --- | --- |
| Agents as Tools | Orchestrator model | Dynamic delegation |
| Graph | Explicit graph structure | Branching/cycles |
| Swarm | Peer agents | Emergent collaboration |
| Workflow | Task dependency graph | Repeatable DAG/pipeline |

Current docs show manual workflow composition and a built-in `strands_tools.workflow` tool.

**Code sample — verified**

~~~python
from strands import Agent

collector = Agent(
    system_prompt="Collect incident evidence.",
    callback_handler=None,
)
analyst = Agent(
    system_prompt="Analyze evidence and separate facts from hypotheses.",
    callback_handler=None,
)
writer = Agent(
    system_prompt="Write a concise incident report.",
)

def process_workflow(incident: str):
    evidence = collector(f"Collect evidence for: {incident}")
    analysis = analyst(f"Analyze this evidence: {evidence}")
    return writer(f"Write the report from this analysis: {analysis}")
~~~

Use Workflow instead of Swarm when a different process path would be a bug.

Runnable lab: [workflow.py](../examples/13-multi-agent-patterns-graph-workflows/workflow.py).

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/multi-agent/graph/
- https://strandsagents.com/docs/user-guide/sdk/multi-agent/graph-components/
- https://strandsagents.com/docs/user-guide/sdk/multi-agent/multi-agent-patterns/
- https://strandsagents.com/docs/user-guide/concepts/agents/session-management/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 14 — Multi-Agent Patterns: Agent Swarms](14-multi-agent-patterns-agent-swarms.md). We will deliberately give agents more routing autonomy, then put hard limits around handoffs, iterations, time, and shared context.

Back to the [course README](../README.md).
