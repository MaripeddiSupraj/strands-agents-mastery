# Lesson 10 — Context Engineering & Context Management

Strands Agents Mastery → Phase 3 — Memory & Context

An agent can remember every message in Python and still fail because the model cannot effectively use an ever-growing context window.

Context engineering is the discipline of deciding what the model should see for the current decision.

Session persistence, which comes next, answers a different question: what should survive after the process or invocation ends?

## Map of this lesson

- Context versus memory versus state
- Why context grows
- The current ContextManager
- auto mode
- agentic mode
- stash and retrieve_context
- Tool-output offloading
- Summarization
- Context cost and relevance
- Security/PII
- Testing context-management behavior

## 1. Context is the model’s working set

A useful analogy:

- session storage = the filing cabinet;
- agent state = application variables;
- context = the papers currently on the desk.

The model can reason only over the information included in its request context.

Typical context includes:

- system instructions;
- conversation messages;
- tool calls/results;
- activated skill instructions;
- injected context;
- multi-agent handoff content.

More context is not automatically better.

## 2. Why context pressure becomes a production problem

Imagine an incident-analysis agent.

Turn 1 returns 8,000 tokens of logs.

Turn 2 returns 10,000 tokens of metrics.

Turn 3 returns a deployment manifest.

Turn 4 repeats status data.

If every byte remains in the model request:

- input token cost grows every turn;
- latency grows;
- relevant evidence competes with noise;
- context-window overflow eventually occurs;
- prompt-injection text from old tool results stays active longer.

The solution is not “buy the model with the biggest context window.” You still need relevance and cost control.

## 3. Current Strands ContextManager

Current Strands exposes context_manager as a first-class Agent parameter.

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent(context_manager="auto")
~~~

The current documentation recommends auto for most agents.

When context_manager is configured, it owns context reduction. Current docs state that a co-provided conversation_manager is ignored.

Do not stack old conversation-reduction patterns with the new ContextManager without understanding which one actually takes effect.

## 4. The strategy-pipeline idea

Current ContextManager runs context-reduction strategies as an ordered pipeline.

Conceptually:

    original messages/tool results
        ↓
    strategy 1
        ↓
    strategy 2
        ↓
    ...
        ↓
    emergency truncation if still overflowing
        ↓
    model input

Order matters because one strategy receives the output of the previous one.

Custom strategy configuration is actively evolving. For exact custom configuration syntax, check the API reference for your pinned SDK rather than copying stale examples.

## 5. auto mode

Current auto mode is designed to work without another model deciding what to compress.

At the time this lesson was verified, the documented defaults include:

- large tool-result offloading/truncation at a tuned threshold;
- a preview kept in context;
- proactive summarization when context utilization reaches a high-water mark;
- recent messages preserved verbatim.

These thresholds are implementation defaults, not architecture constants. Do not encode your application logic around the current numeric values.

The key behavior is:

    large/noisy content
      → moved out of active context
      → concise preview remains
      → full content remains retrievable

and:

    older history under pressure
      → summarized
      → recent conversation retained

## 6. Stash: preserve before reducing

A critical property of the current ContextManager is its stash.

The documentation states that message content is stored before context-reduction strategies act.

That enables offloaded/truncated content to remain retrievable rather than being permanently discarded.

By default the stash is in memory unless configured with durable storage.

This distinction matters:

    compressed out of model context

does not necessarily mean:

    deleted from the application

## 7. retrieve_context

Current context management registers a retrieve_context tool by default when the stash/retrieval path is enabled.

This gives the Agent a way to recover full offloaded content when a preview is insufficient.

The model can therefore work roughly like a human:

    read summary/preview
       ↓
    decide detail is needed
       ↓
    retrieve exact stored context
       ↓
    continue reasoning

This is more efficient than forcing every detail into every model call.

## 8. auto does not mean zero design work

You still choose:

- what tools return;
- how much raw data they fetch;
- which data is sensitive;
- which storage backend holds stashed content;
- retention;
- encryption;
- tenant separation.

A 100,000-line log dump is poor tool design even if auto mode can offload it.

Filter at the source first.

## 9. agentic mode

Current Strands also documents:

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent(context_manager="agentic")
~~~

At the time of verification, agentic context management is documented as experimental.

The model is given more responsibility for deciding:

- what to compress;
- when to compress;
- what to protect.

This can preserve semantically important details better than fixed thresholds in some workloads, but it adds model/tool activity and therefore cost and latency.

Start with auto unless evaluation proves agentic is better for your task.

## 10. Disable context management deliberately

Current Strands supports:

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent(context_manager=False)
~~~

With context management disabled, overflow errors can propagate directly.

This can be appropriate when:

- conversations are guaranteed short;
- you manage context externally;
- you need exact full history and have a strict small bound.

Do not disable it simply because “our model has a big window.”

## 11. Stateful-model limitation

Current ContextManager documentation calls out a limitation with stateful models that manage conversation state server-side.

Setting Strands context_manager with an incompatible stateful model can raise an error.

This is an example of why provider switching requires more than changing the model ID.

Check the current model/provider docs before combining server-side model state with client-side context management.

## 12. Context versus Agent state

Current Strands documents multiple state lifetimes.

Conversation history:

    visible to model as context

Agent state:

    key/value application state
    persists across requests when session-managed
    not automatically prose in model context

Invocation state:

    exists for one invocation
    shared with hooks/tools
    not part of model context by default

Use the smallest scope possible.

A request ID does not need to become prompt text just so a tool can access it.

## 13. Good context engineering starts at tool design

Bad tool:

    get_all_logs(service)
      → 20 MB raw log text

Better:

    search_logs(
        service,
        time_window,
        query,
        max_results
    )
      → bounded evidence

Even better, where appropriate:

    aggregate_errors(...)
      → structured counts
      + representative samples
      + artifact reference

Give the model enough evidence to decide without forcing it to consume the entire data lake.

## 14. Structured context is easier to reason about

Prefer a compact structure:

    service: orders-api
    status: degraded
    error_rate: 8.3%
    window: 10m
    top_error: DB_TIMEOUT
    evidence_ref: obs://...

over 500 lines of prose saying the same thing.

Structure improves:

- token efficiency;
- parsing;
- evaluation;
- redaction;
- downstream provenance.

## 15. Summaries are lossy

Every summary can omit something.

This is why the stash/retrieval path matters.

For safety-critical workflows, keep source evidence outside the summary and preserve references.

A model-generated statement such as:

    “Database latency caused the incident”

must not become the only surviving representation if the raw evidence merely showed correlation.

Keep provenance.

## 16. Security: old untrusted data is still untrusted

Context management does not sanitize prompt injection.

If a malicious ticket or web page contains instructions, summarizing it can:

- retain the malicious instruction;
- distort it;
- accidentally elevate it into apparently trusted summary text.

Keep trust labels/provenance in your application design.

The model should know which content is:

- trusted policy;
- user request;
- retrieved external data;
- tool output.

Hard authorization remains outside model context.

## 17. PII and the stash

Offloading sensitive content from the model window may improve token use, but it still persists the content somewhere.

If you use durable storage, define:

- encryption;
- bucket/key access;
- tenant prefix isolation;
- retention/TTL;
- deletion;
- backup policy;
- audit access.

Do not call something “redacted” merely because it left active model context.

## 18. Durable storage for context artifacts

The unified Strands storage layer currently includes:

- InMemoryStorage;
- LocalFileStorage;
- S3Storage.

For development, local storage is easy to inspect.

For distributed production, S3 can provide durable shared storage, but it adds:

- S3 request/storage cost;
- IAM requirements;
- lifecycle/retention configuration;
- data residency concerns.

Use a dedicated bucket/prefix and least-privilege IAM rather than a broad shared bucket.

## 19. Context Offloader plugin versus ContextManager

Current Strands docs explicitly recommend context_manager="auto" for most agents instead of separately configuring ContextOffloader.

ContextOffloader remains available when you want independent offloading behavior without the full ContextManager.

Do not attach both just because both mention context reduction.

Understand which path owns offloading.

## 20. Token-cost exercise

Take a long multi-tool task and run it twice:

A:

    context_manager=False

B:

    context_manager="auto"

Capture:

- total tokens;
- number of turns;
- latency;
- final answer quality;
- retrieval-tool calls;
- overflow/failure behavior.

The result you want is not merely lower token count. You want acceptable or improved goal success at a lower/bounded context cost.

## 21. Relevance exercise

Create a conversation where an important fact appears early:

    deployment version = 2026.09.14

Then add many irrelevant messages/tool results.

Later ask:

    “Which deployment version are we investigating?”

Verify whether your context strategy retains or successfully retrieves the fact.

This tests information preservation rather than only overflow avoidance.

## 22. Context-management failure modes

### Retrieval fails

The preview may be insufficient. Agent should report uncertainty rather than invent detail.

### Storage disappears

Decide whether the invocation degrades, fails, or requests re-fetching from source.

### Summary drops a key constraint

Evaluation should catch it.

### Sensitive data is stashed indefinitely

Retention control failed even if the prompt stayed small.

### Compression triggers too late

You may still hit provider limits or latency spikes.

## 23. Observability

Track:

- projected/input token growth;
- context utilization where available;
- offload count;
- bytes/tokens offloaded;
- retrieval count;
- summarization events;
- storage errors;
- final goal success;
- token/cost change after context configuration changes.

A sharp increase in retrieve_context calls may indicate previews are too small or tools are too verbose.

## 24. CI/evaluation gate

When changing context strategy:

1. replay long-conversation cases;
2. verify key facts survive;
3. verify tool evidence remains retrievable;
4. compare tokens;
5. compare latency;
6. test malicious retrieved content;
7. test storage failure;
8. verify no cross-session/tenant retrieval.

Context strategy changes can change model behavior as much as prompt changes.

## 25. Production checklist

- [ ] Context and persistent memory are treated as different concerns.
- [ ] auto is the baseline unless evaluation justifies another mode.
- [ ] Tool output is bounded at source.
- [ ] Stash storage has encryption/retention/access policy.
- [ ] Summaries preserve provenance/source references.
- [ ] Untrusted tool data stays labeled as untrusted evidence.
- [ ] Context metrics are observed.
- [ ] Long-conversation regression cases exist.
- [ ] Storage failures are tested.

## Sources checked

- https://strandsagents.com/docs/user-guide/concepts/context-management/
- https://strandsagents.com/docs/user-guide/concepts/context-management/built-in-modes/
- https://strandsagents.com/docs/user-guide/concepts/plugins/context-offloader/
- https://strandsagents.com/docs/user-guide/sdk/agents/state/
- https://strandsagents.com/docs/api/python/strands.agent.agent/
- https://strandsagents.com/docs/api/python/strands.storage.s3_storage/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 11 — Persistent Memory with Session Managers](11-persistent-memory-with-session-managers.md). We will make conversation and Agent state survive process restarts and deployment boundaries.

Back to the [course README](../README.md).
