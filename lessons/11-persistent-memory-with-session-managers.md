# Lesson 11 — Persistent Memory with Session Managers

Strands Agents Mastery → Phase 3 — Memory & Context

Context management keeps the model’s working set useful.

Session management makes Agent state durable across invocations and restarts.

Do not confuse session persistence with semantic long-term memory. A session manager primarily persists conversation/state so an interaction can resume. Knowledge/memory systems that extract reusable facts are a separate layer.

## Map of this lesson

- Session mental model
- What gets persisted
- SnapshotSessionManager
- LocalFileStorage
- S3Storage
- Manual snapshots
- Repository-based File/S3 managers
- Multi-agent caveat
- Session IDs and tenancy
- IAM/security
- Concurrency
- Migration/versioning
- Testing restore behavior


## Recommended hands-on example — Resume the same incident after a restart

> **Build today:** Persist one payments-api incident session, destroy/recreate the Agent process, and resume with the same approved session identity.
>
> **Turn 1:** `INC-2841: payments-api started returning 5xx errors around 10:12 UTC. We found latency increased too.`
>
> **Restart the process**, then run:
>
> **Turn 2:** `Continue INC-2841. What have we already established, and what should we check next?`
>
> **Observe:** which messages/state are restored, where the session is stored, what happens with a wrong session ID, and how session ownership is enforced.
>
> **Why this example:** it clearly separates **context management** (“what the model sees now”) from **session persistence** (“what survives process lifetime”).

A session ID is an identifier, not authentication. Never let users read another incident merely by supplying its ID.


## 1. Without a session manager

A process-local Agent can remember messages while it lives:

    process starts
      ↓
    Agent created
      ↓
    user turn 1
      ↓
    user turn 2
      ↓
    process crashes/redeploys
      ↓
    in-memory Agent is gone

A load-balanced service makes this worse because turn 2 might reach another replica.

Persistence gives the application a stable session identity independent of one process.

## 2. Session management is lifecycle persistence

Current Strands session-management APIs persist Agent conversation/state at lifecycle points and restore it when a session resumes.

For a new single-agent Python workload, current user documentation recommends SnapshotSessionManager.

The snapshot path captures a point-in-time Agent state rather than individually treating every message as the storage primitive.

## 3. SnapshotSessionManager with local storage

**Code sample — verified**

~~~python
from strands import Agent
from strands.session import SnapshotSessionManager
from strands.storage import LocalFileStorage

session_manager = SnapshotSessionManager(
    session_id="test-session",
    storage=LocalFileStorage("./sessions/"),
)

agent = Agent(session_manager=session_manager)
~~~

This is the simplest persistent development setup.

Run one process, send messages, stop it, recreate the Agent with the same session ID/storage, and verify the state restores.

## 4. What a session snapshot represents

Current snapshot documentation’s session preset includes Agent data such as:

- messages;
- Agent state;
- conversation-management state;
- interrupt state;
- model state.

It does not automatically mean “every application field in your database.”

Keep durable business state in the business system of record.

An Agent session is not your order database or ticket database.

## 5. Manual snapshots

Strands also supports explicit snapshots when you want a checkpoint under your own control.

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent(system_prompt="You are a helpful assistant")
agent("Hello!")
agent.state.set("user_id", "user-123")

snapshot = agent.take_snapshot(preset="session")

print(snapshot.schema_version)
print(snapshot.created_at)
print(snapshot.data.keys())
~~~

Session managers automate persistence. Manual snapshots are useful when you need precise checkpoints/restore logic.

## 6. Restore a manual snapshot

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent(system_prompt="You are a helpful assistant")
agent("Hello!")

snapshot = agent.take_snapshot(preset="session")

agent("Tell me a joke")
agent("Tell me another one")

agent.load_snapshot(snapshot)

print(len(agent.messages))
~~~

Only fields present in the snapshot are restored. Read the current snapshot reference if you customize include/exclude fields.

## 7. Immutable checkpoints

Current SnapshotSessionManager supports append-only immutable snapshots when a configured snapshot trigger fires.

This enables time-travel-style restore instead of only the mutable latest state.

Use cases:

- checkpoint before a risky workflow stage;
- audit/replay;
- debugging a regression.

Immutable history also increases storage and retention obligations. Decide how long checkpoints should live.

## 8. Local filesystem is not a distributed session store

LocalFileStorage is excellent for:

- learning;
- local development;
- single-host debug;
- tests.

It is risky for:

- multiple ECS tasks;
- multiple EKS pods;
- ephemeral container filesystems;
- Lambda;
- cross-region failover.

In a horizontally scaled service, session data must be available to whichever replica owns/resumes the session.

## 9. S3-backed snapshot storage

Current unified storage includes S3Storage.

**Code sample — illustrative**

Both APIs are verified; this composition is course-authored.

~~~python
from strands import Agent
from strands.session import SnapshotSessionManager
from strands.storage import S3Storage

storage = S3Storage(
    "my-agent-sessions",
    prefix="prod/sessions/",
    region_name="us-east-1",
)

session_manager = SnapshotSessionManager(
    session_id="session-123",
    storage=storage,
)

agent = Agent(session_manager=session_manager)
~~~

Use your real region and a dedicated bucket/prefix.

Do not hard-code a shared user ID as the session ID.

## 10. Least-privilege S3 access

The current S3Storage implementation needs to write, read, delete, and list objects for its configured namespace.

Translate that into the minimum S3 IAM permissions for your chosen bucket/prefix.

Do not grant s3:* on every bucket.

A practical policy design separates:

- bucket-level listing limited to the session prefix;
- object-level read/write/delete limited to that prefix.

Exact IAM resource statements depend on your bucket layout and organization controls, so validate with AWS IAM Access Analyzer and the current S3 IAM reference.

Encrypt the bucket, block public access, and enable access logging/auditing according to your platform policy.

## 11. Repository-based session managers

Python also retains repository-style session managers such as FileSessionManager and S3SessionManager.

Current FileSessionManager constructor:

**Code sample — verified**

~~~python
from strands.session import FileSessionManager

session_manager = FileSessionManager(
    session_id="multi-agent-session",
)
~~~

It persists message/Agent metadata in repository-style storage.

Current S3SessionManager remains available for S3-backed repository-style sessions.

**Code sample — verified**

~~~python
from strands.session import S3SessionManager

session_manager = S3SessionManager(
    session_id="session-123",
    bucket="my-agent-sessions",
    region_name="us-east-1",
)
~~~

For new single-agent Python sessions, prefer the current SnapshotSessionManager recommendation unless you need repository-format compatibility or another documented case.

## 12. Important current-doc caveat for Graph/Swarm

Strands is moving quickly here.

As verified on 2026-09-22:

- the current session-management user guide explicitly says Python SnapshotSessionManager does not support Graph/Swarm and recommends a repository-based manager on the orchestrator;
- the latest Python SnapshotSessionManager API page also contains newer wording about multi-agent latest-state behavior.

Those official pages are not perfectly reconciled.

For this course, we take the conservative documented path:

> For Python Graph/Swarm examples, use the repository-based session-manager path on the orchestrator unless the current user guide/API has been reconciled in the SDK version you pin.

This is exactly the kind of fast-moving area where you should check the API reference and release notes rather than guess.

## 13. Child Agents should not each invent independent session ownership

For a multi-agent orchestrator, session persistence should be designed at the orchestration boundary.

Current user guidance warns against attaching independent session managers to child Agents in Graph/Swarm repository-based persistence.

Why?

Because otherwise you create multiple independently durable histories that may not represent one coherent orchestration checkpoint.

Lesson 13 will revisit this for Graph.

## 14. Session IDs are security boundaries

Never let a user pick an arbitrary session ID and then load it without authorization.

Bad:

    GET /chat?session_id=customer-B

with no ownership check.

A secure session lookup uses authenticated identity:

    authenticated principal
       ↓
    authorize ownership/access to session
       ↓
    derive/lookup internal session key
       ↓
    load session

Treat session ID as an identifier, not a secret and not proof of access.

## 15. Tenant isolation in storage

For multi-tenant systems, design storage namespaces deliberately.

Example conceptual key shape:

    environment/
      tenant-id/
        user-id/
          session-id/

But do not trust path fragments directly from unvalidated user strings.

Keep application metadata that maps external/public IDs to internal storage IDs.

Use IAM boundaries so one service/tenant cannot read unrelated prefixes when your architecture supports that separation.

## 16. PII retention

Persistent conversation history can contain:

- customer names;
- email;
- account IDs;
- logs;
- support content;
- sensitive operational data.

Define:

- retention period;
- deletion request behavior;
- legal/compliance basis;
- encryption;
- regional residency;
- backup retention;
- access/audit policy.

“Agent memory” is still stored customer data.

## 17. Trusted snapshot warning

Current Strands snapshot docs contain a security warning: snapshots restore messages verbatim, including tool-call content.

That means you must load snapshots only from a source you control.

A maliciously modified message history is not passive text. In Python, certain trailing tool-call content in restored history can lead to tool execution on the next invocation.

Protect session storage from user-controlled writes and integrity tampering.

## 18. Encrypt and validate storage

For S3-backed sessions:

- SSE-KMS when your policy requires customer-managed key control;
- bucket policy to deny public access;
- TLS;
- versioning where useful;
- object lifecycle rules;
- access logs/CloudTrail data events when required;
- scoped runtime IAM.

Application-level integrity/version checks may also be appropriate for high-assurance systems.

## 19. Concurrency and sessions

Persistence does not automatically solve concurrent updates.

Two requests for the same logical session at the same time can still create race conditions.

Recall Lesson 03: one stateful Agent instance rejects overlapping unrelated invocations by default.

At service scale, add a session-level concurrency strategy such as:

- route/lock one active request per session;
- optimistic version checks;
- queue turns for the same session.

Do not allow two replicas to independently mutate one conversation without a defined conflict model.

## 20. Session restore must be version-aware

Your deployed application changes over time:

    v1 session
      ↓
    deploy v2
      ↓
    v2 loads old snapshot

Potential breakage:

- tool names changed;
- state schema changed;
- model provider changed;
- prompt changed;
- plugin no longer exists.

Version your application/session schema where needed and test backward compatibility.

A session should not be allowed to revive a retired privileged tool by loading stale state.

## 21. Sessions and context management work together

Session manager answers:

    What survives?

Context manager answers:

    What is sent to the model now?

A durable session can contain far more history than should be sent on every turn.

Use both:

    durable session store
       ↓
    restored Agent state
       ↓
    ContextManager selects/compresses working set
       ↓
    model call

This is the normal enterprise shape.

## 22. Session persistence is not long-term semantic memory

Saving the raw conversation does not automatically create useful long-term knowledge.

For example:

    “The user prefers Terraform.”

A session manager can preserve the message where that appeared.

A semantic memory system might extract that as a retrievable fact across future sessions.

Strands also has memory-related integrations, but that is a separate architecture from simple session resumption.

Do not promise “memory” when you really mean “we store chat history.”

## 23. Observability

Track:

- session create/resume;
- session storage read/write latency;
- storage failures;
- snapshot size;
- checkpoint count;
- restore failures;
- concurrent-session conflict;
- session schema version;
- age/retention.

Do not use raw session IDs containing customer identifiers as public metric labels.

## 24. Testing

### Restart test

1. invoke Agent;
2. terminate process;
3. recreate Agent with same session;
4. verify continuity.

### Isolation test

Two session IDs must not see each other’s messages/state.

### Authorization test

User A cannot request User B’s session.

### Corruption test

Malformed session data fails safely.

### Upgrade test

Current code restores the prior release’s test fixture.

### Concurrency test

Two simultaneous turns for one session follow your chosen serialization/conflict policy.

### Retention test

Expired/deleted sessions are really unavailable from primary and defined backup paths according to policy.

## 25. Cost awareness

Session storage introduces:

- S3 GET/PUT/LIST/storage charges;
- snapshot growth;
- backup/versioning cost;
- KMS calls where applicable.

More importantly, restoring a large session does not mean sending every saved message to the model. Use context management to control model-token cost.

## 26. CI/CD and IaC

Provision production session storage with IaC.

Terraform/CloudFormation should define:

- bucket;
- encryption;
- public-access block;
- lifecycle;
- IAM role/policy;
- logging/audit configuration;
- tags;
- region.

Do not create the bucket manually and then let the Agent runtime depend on undocumented permissions.

Lesson 19/20 will put this into a deployable architecture.

## 27. Production checklist

- [ ] SnapshotSessionManager is used for new single-agent Python sessions unless another documented requirement applies.
- [ ] Local storage is not used accidentally for horizontally scaled production.
- [ ] Session ownership is authorized.
- [ ] Tenant namespaces are isolated.
- [ ] S3 IAM is prefix-scoped and least privilege.
- [ ] PII retention/deletion policy exists.
- [ ] Snapshots are loaded only from trusted storage.
- [ ] Same-session concurrency is controlled.
- [ ] Session schema/version upgrades are tested.
- [ ] Context management limits what restored history reaches the model.


## 27. State: conversation history, Agent state, and invocation state are different

Current Strands explicitly separates:

1. **Conversation history** — model-visible messages.
2. **Agent/app state** — key-value state outside model context, maintained across requests.
3. **Invocation state** — request-scoped data that survives loop cycles for one invocation and is not automatically placed in model context.

**Code sample — verified**

~~~python
from strands import Agent, ToolContext, tool

@tool(context=True)
def whoami(tool_context: ToolContext) -> str:
    """Return trusted user ID from invocation state."""
    user_id = tool_context.invocation_state.get("user_id", "unknown")
    return f"Current user: {user_id}"

agent = Agent(tools=[whoami])

result = agent(
    "Who am I?",
    invocation_state={"request_id": "r-42", "user_id": "u-1"},
)
~~~

Keep trusted identity/tenant metadata in application state rather than natural-language prompts where possible.

Runnable lab: [state.py](../examples/11-persistent-memory-with-session-managers/state.py).

## 28. Session persistence is not long-term memory

A **SessionManager** persists a conversation so that session can resume.

A **MemoryManager** carries durable knowledge across different sessions without replaying old conversations. Current MemoryManager supports recall, automatic injection, and optional writes/extraction through memory stores.

**Code sample — verified**

~~~python
from strands import Agent
from strands.memory import MemoryManager
from strands.vended_memory_stores.test_memory_store import TestMemoryStore

store = TestMemoryStore(name="incident-notes")

agent = Agent(
    memory_manager=MemoryManager(stores=[store]),
)
~~~

The test store is for learning/tests. Current Strands also provides a Bedrock Knowledge Base store for a managed production backend and supports custom stores.

Memory writing is opt-in. Scope stores by tenant, define retention/deletion, and do not automatically remember secrets or PII.

Runnable lab: [long_term_memory.py](../examples/11-persistent-memory-with-session-managers/long_term_memory.py).

## Sources checked

- https://strandsagents.com/docs/user-guide/concepts/agents/session-management/
- https://strandsagents.com/docs/api/python/strands.session.snapshot_session_manager/
- https://strandsagents.com/docs/api/python/strands.session.file_session_manager/
- https://strandsagents.com/docs/api/python/strands.session.s3_session_manager/
- https://strandsagents.com/docs/api/python/strands.storage.s3_storage/
- https://strandsagents.com/docs/user-guide/sdk/agents/snapshots/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 12 — Multi-Agent Patterns: Agents as Tools](12-multi-agent-patterns-agents-as-tools.md). Now that one Agent can be bounded, context-managed, and persisted, we can safely introduce specialist Agents.

Back to the [course README](../README.md).
