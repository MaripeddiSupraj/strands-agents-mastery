# Lesson 15 — Agent2Agent (A2A): Talking to Remote Agents

Strands Agents Mastery → Phase 4 — Multi-Agent Systems

Agents-as-Tools, Graph, and Swarm can all run inside one process.

Agent2Agent, or A2A, is for a different boundary:

    Agent/service A
       ↓ network
    remote Agent/service B

The remote Agent can be independently deployed, scaled, owned, authenticated, and upgraded.

That makes A2A useful for distributed agent systems.

It also gives you all the normal problems of distributed systems: network failure, authentication, authorization, timeouts, versioning, observability, and tenant isolation.

## Map of this lesson

- What A2A solves
- Installing current A2A support
- A2AAgent client
- Timeouts and authentication surface
- Streaming
- Agent cards
- Using a remote Agent as a tool
- Graph support
- Current Swarm limitation
- Creating A2AServer
- Conversation isolation
- Context IDs are not authentication
- Production security
- Failure handling
- Observability
- Testing and deployment


## Recommended hands-on example — Move one specialist behind a real service boundary

> **Build today:** Keep the Incident Commander local, but deploy a Security/Compliance specialist separately and call it through A2A.
>
> **Run:** `INC-2841 contains repeated authentication failures. Ask the remote security specialist what evidence should be checked, then summarize it with the incident context.`
>
> **Observe:** remote Agent discovery/connection, authentication, network latency, timeout behavior, trace correlation, and what happens when the remote Agent is unavailable.
>
> **Why this example:** the concept becomes obvious when the learner sees the boundary change from “child Agent in my process” to “independently deployed service owned/scaled/versioned separately.”

Treat A2A `context_id`/conversation identifiers as protocol state, not authentication or tenant authorization.


## 1. What A2A changes

Local specialist:

    parent Agent
      ↓ function/tool boundary
    child Agent
      ↓
    same process

A2A specialist:

    parent service
      ↓ HTTP/A2A protocol
    remote Agent service
      ↓
    separate process/runtime/account/network if you choose

This gives you a stronger architecture boundary.

It can also give the remote Agent a distinct IAM role and deployment lifecycle.

## 2. Install A2A support

Current Strands Python documentation installs the A2A dependencies with an optional extra.

**Code sample — verified**

~~~bash
pip install 'strands-agents[a2a]'
~~~

Pin the package version in production.

The protocol and SDK evolve, so run compatibility tests when either side upgrades.

## 3. Consume a remote Agent

Current Strands exposes A2AAgent.

**Code sample — verified**

~~~python
from strands.agent.a2a_agent import A2AAgent

a2a_agent = A2AAgent(
    endpoint="http://localhost:9000",
)

result = a2a_agent("Show me 10 ^ 6")
print(result.message)
~~~

A2AAgent returns an AgentResult-style result, which makes it easier to compose with code that already handles Agent results.

For production, use HTTPS/private network controls as appropriate rather than a plaintext localhost-style endpoint.

## 4. Current A2AAgent configuration

At the time this lesson was verified, the Python constructor documents:

- endpoint: required base URL;
- name: optional;
- description: optional;
- timeout: HTTP operations timeout, default 300 seconds;
- client_config: configuration for authenticated transport.

Current docs state that client_config can be used for authenticated transports such as SigV4, OAuth, or bearer-token approaches through a configured HTTP client.

The older a2a_client_factory parameter is deprecated.

Authentication setup is transport-specific. Use the current ClientConfig/A2A documentation for exact syntax instead of copying stale code.

## 5. Do not accept a five-minute remote timeout blindly

The documented default timeout is generous.

Your service may have a 30-second or 60-second user-facing SLO.

Set remote timeouts intentionally so that:

    caller deadline
       >
    remote A2A timeout
       >
    remote Agent/tool sub-timeouts

leaves room for cleanup/error handling.

A timeout should be part of the end-to-end latency budget.

## 6. Remote Agent invocation is still a network call

Expect:

- DNS failure;
- TLS failure;
- connection refusal;
- authentication failure;
- 5xx;
- throttling;
- partial streaming disconnect;
- remote Agent timeout.

Classify errors.

Do not retry every failure indiscriminately.

A remote Agent may have executed a side effect before the connection broke.

## 7. Idempotency must cross the network boundary

If a remote Agent can perform writes, design a business-level idempotency key.

Example:

    change_request_id = CR-12345

The client retry should carry the same logical operation identity so the remote service/downstream tool can detect duplicates.

Do not assume A2A transport retry automatically makes business side effects safe.

## 8. Async invocation

Current Python A2AAgent supports invoke_async.

**Code sample — verified**

~~~python
import asyncio
from strands.agent.a2a_agent import A2AAgent

async def main():
    a2a_agent = A2AAgent(
        endpoint="http://localhost:9000",
    )

    result = await a2a_agent.invoke_async(
        "Calculate the square root of 144"
    )
    print(result.message)

asyncio.run(main())
~~~

Use async invocation naturally inside async services rather than blocking the event loop.

## 9. Streaming a remote Agent

Current Python A2AAgent also supports stream_async.

**Code sample — verified**

~~~python
import asyncio
from strands.agent.a2a_agent import A2AAgent

async def main():
    a2a_agent = A2AAgent(
        endpoint="http://localhost:9000",
    )

    async for event in a2a_agent.stream_async(
        "Explain quantum computing"
    ):
        if "data" in event:
            print(event["data"], end="", flush=True)

asyncio.run(main())
~~~

Apply the Lesson 06 rules:

- do not expose raw protocol events blindly;
- handle disconnect/cancellation;
- treat partial output as non-final;
- protect PII.

## 10. Agent cards provide discovery metadata

A2A servers publish an Agent Card describing the remote Agent and its capabilities.

Current Strands server documentation exposes the card at:

    /.well-known/agent-card.json

A client can use card metadata for discovery.

Treat metadata from an external service as untrusted input until you trust/authenticate the endpoint.

Do not automatically grant privileges because a remote Agent card says:

    “I am the production admin agent.”

Identity must come from transport/service trust, not self-description.

## 11. Use A2AAgent as an orchestrator tool

Current Strands supports wrapping a remote Agent in a normal tool.

**Code sample — verified**

~~~python
from strands import Agent, tool
from strands.agent.a2a_agent import A2AAgent

calculator_agent = A2AAgent(
    endpoint="http://calculator-service:9000",
    name="calculator",
)

@tool
def calculate(expression: str) -> str:
    """Perform a mathematical calculation."""
    result = calculator_agent(expression)
    return str(result.message["content"][0]["text"])

orchestrator = Agent(
    system_prompt=(
        "You are a helpful assistant. "
        "Use the calculate tool for math."
    ),
    tools=[calculate],
)
~~~

This combines the familiar Agents-as-Tools design with a network boundary.

## 12. Why A2A can improve privilege isolation

Suppose the parent Agent only needs read-only AWS permissions.

The remote deployment Agent needs permission to update one ECS service.

You can deploy:

    parent service role
      → no ECS update permission
      → allowed to authenticate to A2A service

    deployment A2A service role
      → ecs update permission only for approved services

Now the remote service can enforce its own authorization and audit trail.

This is stronger than putting every AWS permission on one process.

## 13. Python Graph currently supports A2AAgent nodes

Current Strands documentation supports A2AAgent inside Python Graph workflows.

That makes a distributed deterministic flow possible:

    local intake
      ↓
    remote security Agent
      ↓
    remote deployment Agent
      ↓
    local verification Agent

Use the current Graph/A2A example for exact constructor wiring in your pinned release.

Do not assume every multi-agent pattern accepts remote Agents.

## 14. A2AAgent is not currently supported in Swarm

At the time this lesson was verified, current Strands documentation explicitly says A2AAgent is not supported in Swarm in either SDK.

The reason given is that Swarm handoff behavior needs capabilities not currently available through the A2A protocol integration.

Use:

- Agents-as-Tools; or
- Python Graph

for remote A2A composition today.

Check the live docs on upgrade because this may change.

## 15. Create an A2A server

Current Python Strands exposes A2AServer from strands.multiagent.a2a.

The recommended current pattern is an agent_factory that creates a fresh Agent per A2A context.

**Code sample — verified**

~~~python
import logging

from strands import Agent
from strands.multiagent.a2a import A2AServer
from strands.vended_tools import notebook

logging.basicConfig(level=logging.INFO)

def create_agent(context_id: str) -> Agent:
    return Agent(
        name="Notebook Agent",
        description=(
            "A note-taking agent that organizes information in notebooks."
        ),
        tools=[notebook],
        callback_handler=None,
    )

a2a_server = A2AServer(
    agent_factory=create_agent,
)

a2a_server.serve()
~~~

The example demonstrates the important design: one Agent instance per conversation context.

## 16. Why agent_factory matters

Current A2A server documentation recommends agent_factory rather than a single shared Agent.

Each context gets a dedicated Agent.

Benefits:

- conversation histories stay separate;
- multiple contexts can run concurrently;
- per-context session persistence can be wired in the factory;
- one caller does not mutate another caller's in-memory Agent.

Current docs mark the single shared agent mode as deprecated for this use.

## 17. context_id isolates conversation state, not identity

This is one of the most important current A2A warnings.

The documentation explicitly states that context_id is not an authentication boundary.

A caller who can provide another caller's context ID could attach to that conversation unless your transport/gateway authorization prevents it.

Therefore:

    authenticate caller
       ↓
    authorize caller to business/session identity
       ↓
    map to allowed A2A context
       ↓
    process request

Do not use possession of a context ID as proof of access.

## 18. Limit retained server contexts

Current A2AServer exposes max_contexts and documents a default of 1000 retained contexts.

When the cap is exceeded, least-recently-used contexts can be evicted; a later request may begin with a fresh in-memory Agent unless durable session state is wired.

Tune memory bounds.

If conversation continuity matters beyond process memory, add a proper session manager per context in the agent factory using the current supported session pattern.

## 19. Streaming mode is evolving

Current A2AServer configuration documents enable_a2a_compliant_streaming.

At the time of verification, the current default still uses legacy status-update streaming with a warning, while enabling the option uses A2A-compliant artifact updates and is planned to become the default in a future major version.

This is exactly the kind of version-specific behavior to check during upgrades.

Do not build clients that depend on undocumented legacy event details.

## 20. Put authentication in front of the server

The built-in server demonstrates A2A protocol serving; production authentication/authorization belongs in your deployment architecture.

Possible patterns include:

- private service networking;
- mTLS/service mesh;
- signed AWS requests where supported by your transport;
- OAuth/bearer access at a gateway;
- identity-aware reverse proxy.

Use the current A2A ClientConfig/server deployment docs for exact integration details.

Do not expose a privileged A2A Agent unauthenticated on a public endpoint.

## 21. Authorization must still exist inside the remote service

Even an authenticated caller should not automatically have every tool.

The A2A service should enforce:

- caller/tenant;
- environment;
- resource scope;
- operation type;
- approval state;
- rate/quota.

A remote deployment Agent should not accept:

    “delete every cluster”

just because the request came over a valid A2A connection.

## 22. PII and data residency now cross a service boundary

Before sending a prompt to a remote Agent, ask:

- what data is included?
- where is the remote service hosted?
- which model/provider does it use?
- what does it log?
- what does its session manager persist?
- what trace backend receives its data?

A2A makes architecture modular; it does not make data governance disappear.

## 23. Distributed tracing

Carry a safe correlation identifier across:

    incoming API
      ↓
    parent Agent
      ↓
    A2A HTTP call
      ↓
    remote Agent
      ↓
    remote tool/API

Use OpenTelemetry-compatible propagation where your transport/instrumentation supports it.

Then an incident can be traced end-to-end.

Avoid putting raw customer identifiers into trace attributes.

## 24. Measure the network boundary

Track:

Client side:

- remote Agent endpoint logical name;
- call duration;
- timeout;
- transport status/error;
- retry count.

Server side:

- context count;
- request duration;
- Agent turns/tokens;
- tool failures;
- context eviction;
- auth denial.

End-to-end:

- goal success;
- total latency;
- total cost.

## 25. Health checks should not invoke expensive reasoning

A load balancer health endpoint should verify service readiness, not run a full model conversation.

Separate:

    process/network readiness

from:

    deep synthetic Agent test

Deep Agent probes can run periodically from monitoring, not on every load balancer check.

## 26. Compatibility testing

A2A introduces two independently deployed versions.

Test:

- client old / server new;
- client new / server old;
- Agent card changes;
- auth change;
- streaming change;
- timeout behavior;
- session restore;
- malformed protocol response.

Pin compatible versions and deploy canaries.

## 27. Failure exercise

Run the example A2A server and client locally.

Then:

1. stop the server mid-call;
2. use an invalid endpoint;
3. set a small client timeout;
4. send two different conversation contexts;
5. verify they do not share history;
6. attempt to resume a context through your application without authorization and make sure your app rejects it.

The final test is application security, not SDK behavior.

## 28. Deployment architecture example

A production AWS shape could be:

    API / parent Agent
       ↓ private/authenticated call
    A2A specialist on AgentCore/ECS/EKS
       ↓ specialist IAM role
    downstream AWS/API resource

Provision with IaC:

- service/runtime;
- IAM role;
- network policy/security group;
- secrets;
- observability;
- scaling;
- alarms.

Lesson 19 covers deployment targets.

## 29. Production checklist

- [ ] A2A package/API usage matches the pinned current SDK.
- [ ] Remote endpoints use approved authenticated transport.
- [ ] context_id is never treated as authentication.
- [ ] agent_factory isolates conversations.
- [ ] max_contexts is intentionally configured.
- [ ] Client and server timeouts fit the end-to-end SLO.
- [ ] Write operations use business-level idempotency.
- [ ] Remote service has least-privilege runtime identity.
- [ ] Cross-service PII/residency is reviewed.
- [ ] Distributed traces/correlation exist.
- [ ] Compatibility tests cover independent upgrades.
- [ ] Current pattern limitations, including Swarm support, are checked on upgrade.

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/multi-agent/agent-to-agent/
- https://strandsagents.com/docs/user-guide/sdk/multi-agent/a2a-server-configuration/
- https://strandsagents.com/docs/user-guide/sdk/multi-agent/agents-as-tools/
- https://strandsagents.com/docs/user-guide/sdk/multi-agent/graph/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 16 — Evaluating Agents](16-evaluating-agents.md). We will stop judging agents by impressive demos and build repeatable evaluation gates for outputs, tools, trajectories, safety, cost, and regressions.

Back to the [course README](../README.md).
