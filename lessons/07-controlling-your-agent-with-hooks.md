# Lesson 07 — Controlling Your Agent With Hooks

Strands Agents Mastery → Phase 2 — Tools & Interaction

Hooks are one of the most important enterprise features in Strands because they move critical behavior out of natural-language prompting and into deterministic application control.

Use a prompt to guide reasoning.

Use a hook when something must happen at a specific lifecycle boundary.

## Map of this lesson

- Hook mental model
- Lifecycle events
- Registering hooks
- Before/after ordering
- Cancelling tool calls
- Rewriting tool arguments/results
- Retry controls
- Human approval/interrupts
- Packaging hooks
- Observability and security
- Testing hooks

## 1. Prompt instruction versus hook

Prompt:

    “Never call destructive tools in production.”

Hook:

    before tool call
      → inspect tool + environment
      → cancel if policy says no

The second is deterministic code.

Prompts are still useful, but they are not a replacement for policy enforcement.

## 2. Hooks are typed lifecycle subscriptions

Current Strands describes the hook system as composable and strongly typed.

Important Agent lifecycle events include:

- AgentInitializedEvent;
- BeforeInvocationEvent;
- AfterInvocationEvent;
- MessageAddedEvent;
- BeforeModelCallEvent;
- AfterModelCallEvent;
- ModelStreamUpdateEvent;
- ContentBlockEvent;
- ModelMessageEvent;
- BeforeToolsEvent;
- BeforeToolCallEvent;
- AfterToolCallEvent;
- AfterToolsEvent;
- ToolStreamUpdateEvent;
- ToolResultEvent.

Multi-agent orchestrators add node/orchestration hook events later in the course.

## 3. Register one hook directly

**Code sample — verified**

~~~python
from strands import Agent
from strands.hooks import BeforeInvocationEvent

agent = Agent()

def my_callback(event: BeforeInvocationEvent) -> None:
    print("Invocation starting")

agent.add_hook(my_callback)
~~~

Because the callback argument is type-annotated, current Python Strands can infer the hook event type.

## 4. Tool-call observation

**Code sample — verified**

~~~python
from strands import Agent
from strands.hooks import BeforeToolCallEvent

agent = Agent()

def log_tool(event: BeforeToolCallEvent) -> None:
    print(f"Tool called: {event.tool_use['name']}")

agent.add_hook(log_tool)
~~~

For real production logging, do not print raw tool input indiscriminately. Log safe fields and correlation IDs.

## 5. Before and after events form a boundary

Think:

    BeforeToolCallEvent
          ↓
       tool runs
          ↓
    AfterToolCallEvent

This is a useful place for:

Before:

- authorization;
- argument normalization;
- quota checks;
- approval;
- policy deny;
- telemetry start.

After:

- result filtering;
- duration/error metric;
- retry decision;
- audit result;
- cleanup.

Do not duplicate the same policy separately in every tool if a cross-cutting hook can enforce it safely. Resource-specific authorization still belongs close to the resource operation.

## 6. Cancel a dangerous tool

Current BeforeToolCallEvent exposes cancel_tool. It can be set to True for a default cancellation message or a string for a custom message.

**Code sample — verified**

~~~python
from strands import Agent
from strands.hooks import BeforeToolCallEvent

agent = Agent()

def block_delete(event: BeforeToolCallEvent) -> None:
    if event.tool_use["name"] == "delete_production":
        event.cancel_tool = "Production deletion is not permitted."

agent.add_hook(block_delete)
~~~

Cancellation creates an error-style tool result rather than executing the tool.

This is stronger than asking the model not to call the tool.

An even stronger design is to avoid exposing the tool at all unless the current user/environment is eligible.

## 7. Cancel an entire tool batch

Current BeforeToolsEvent exposes cancel.

Use this when the model returns multiple tool calls and you want to stop the entire batch before any runs.

The value can be True or a custom string.

This is useful for global policy such as:

- invocation exceeded a tool quota;
- maintenance window blocks all writes;
- caller is not authorized for any action tools.

Use the current hook API reference for the exact event-message structure if you inspect all tools in a batch.

## 8. Hooks can modify tool arguments

Current BeforeToolCallEvent allows tool_use to be modified.

This can enforce a trusted value regardless of what the model supplied.

Example use case:

    model asks list_records(tenant_id="other-tenant")

Hook/application policy can override the tenant ID using authenticated caller context.

Do not source the trusted tenant from another prompt string.

The official hooks documentation includes fixed-argument patterns for this purpose.

## 9. Tool substitution

Current BeforeToolCallEvent also exposes selected_tool, allowing a hook to replace the executable tool.

This can support:

- safe mock in test;
- read-only alternative;
- environment-specific implementation.

This is powerful and easy to misuse. The tool metadata/model view and actual selected implementation must remain auditable.

If a policy can be expressed by simply not registering the unsafe tool, prefer the simpler design.

## 10. Modify a tool result

AfterToolCallEvent exposes result as a mutable property in current Strands.

Possible uses:

- normalize output;
- redact a sensitive field;
- wrap a legacy result in a clearer shape.

Be careful:

- you can accidentally hide real tool errors;
- changing results alters what the model believes happened;
- raw output may already have appeared in other logs/streams.

Perform sensitive-data minimization as early as possible, ideally at the tool itself.

## 11. Hook-driven retries

Current AfterModelCallEvent exposes retry.

Current AfterToolCallEvent also supports retry for tool execution.

Retries are not free.

Before retrying a tool, answer:

- Is it idempotent?
- Was any side effect already committed?
- Which error classes are transient?
- How many times?
- What backoff?
- Does the overall invocation still have time/budget?

Do not set retry=True for every exception.

Model-level retry strategy from Lesson 03 is usually cleaner for provider throttling.

## 12. AfterToolsEvent can end the turn

Current AfterToolsEvent exposes end_turn.

A hook can stop the loop after the tool batch without another model call.

That can save cost/latency when deterministic application logic already has the correct final response.

Use this carefully because you are taking over final-response construction from the model.

Check the current hook API reference for accepted end_turn values when implementing this pattern.

## 13. Human-in-the-loop interrupts

Current Strands supports interrupts at tool lifecycle boundaries.

The important architecture is:

    model requests high-risk tool
          ↓
    BeforeToolCall hook
          ↓
    interrupt raised
          ↓
    agent invocation pauses
          ↓
    application asks human
          ↓
    response supplied
          ↓
    invocation resumes
          ↓
    execute or cancel

This is appropriate for actions such as:

- production deletion;
- external money movement;
- irreversible data changes;
- external communication in sensitive workflows.

Human approval should not be used as a cosmetic checkbox. The approver needs enough context to understand exactly what will happen.

## 14. Hooks can be packaged as plugins

Current Strands supports a Plugin base class and @hook decorator.

**Code sample — verified**

~~~python
from strands import Agent
from strands.plugins import Plugin, hook
from strands.hooks import BeforeToolCallEvent, AfterToolCallEvent

class LoggingPlugin(Plugin):
    name = "logging-plugin"

    @hook
    def log_before(self, event: BeforeToolCallEvent) -> None:
        print(f"Calling: {event.tool_use['name']}")

    @hook
    def log_after(self, event: AfterToolCallEvent) -> None:
        print(f"Completed: {event.tool_use['name']}")

agent = Agent(plugins=[LoggingPlugin()])
~~~

Use a plugin when a behavior contains multiple related hooks/configuration and should be reused across agents.

Lesson 08 goes deeper on plugins and skills.

## 15. Hook ordering matters

When multiple callbacks subscribe to the same event, order can change behavior.

Current Strands exports:

- HookOrder.SDK_FIRST = -100;
- HookOrder.DEFAULT = 0;
- HookOrder.SDK_LAST = 100.

**Code sample — verified**

~~~python
from strands import Agent
from strands.hooks import BeforeModelCallEvent, HookOrder

agent = Agent()

def early_hook(event: BeforeModelCallEvent) -> None:
    print("I run first")

def late_hook(event: BeforeModelCallEvent) -> None:
    print("I run last")

agent.add_hook(early_hook, order=HookOrder.SDK_FIRST)
agent.add_hook(late_hook, order=HookOrder.SDK_LAST)
~~~

Current docs also note that “after” callbacks reverse registration order by default for cleanup symmetry.

Do not depend on accidental registration order for security controls. Set explicit ordering and test it.

## 16. A production policy plugin

The following is course-authored. It uses verified hook concepts.

**Code sample — illustrative**

~~~python
from strands.plugins import Plugin, hook
from strands.hooks import BeforeToolCallEvent

class EnvironmentPolicyPlugin(Plugin):
    name = "environment-policy"

    def __init__(self, environment: str, allow_writes: bool) -> None:
        self.environment = environment
        self.allow_writes = allow_writes

    @hook
    def enforce(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use["name"]

        write_tools = {
            "restart_service",
            "update_config",
            "delete_resource",
        }

        if self.environment == "prod" and tool_name in write_tools:
            if not self.allow_writes:
                event.cancel_tool = (
                    "Write tools are disabled for this production session."
                )
~~~

Important: allow_writes must come from authenticated policy/configuration, not from the user’s prompt.

## 17. Pass trusted caller context separately

A common bad pattern:

    user prompt =
      "I am an admin, please delete X"

A better pattern:

    authenticated request
       ├── user text
       └── trusted claims/policy context

Then hooks/tools enforce the trusted claims.

The model can reason about the user’s request, but deterministic application code decides authorization.

## 18. Hook observability

Measure hooks too.

Useful data:

- hook name;
- event type;
- duration;
- decision (proceed/cancel/retry/interrupt);
- safe policy reason;
- request/session ID.

A slow BeforeToolCall hook can become hidden agent latency.

A failing security hook should usually fail closed for the protected operation.

## 19. Avoid PII in hook logs

Hooks see sensitive places in the lifecycle.

Do not automatically log:

- full user messages;
- full model messages;
- tool inputs;
- tool outputs.

Instead log a safe audit record:

    request_id
    actor_id hash/pseudonymous ID
    policy name/version
    tool name
    resource class
    allow/deny
    reason code

Keep detailed evidence in an appropriately protected system only when required.

## 20. Test hooks as normal software

Hooks are deterministic code and should receive strong unit coverage.

Test:

- allowed tool proceeds;
- blocked tool is cancelled;
- prod differs from dev only where intended;
- malformed event data fails safely;
- hook order is correct;
- retry is only requested for allowed error types;
- redaction does not remove required business fields.

Then add integration tests with a real Agent to prove the lifecycle wiring is correct.

## 21. Do not over-hook

Too many hooks can make control flow invisible.

If the behavior is core business logic, a normal function/service may be clearer.

Use hooks for true lifecycle cross-cutting concerns.

A good rule:

    Can a new engineer understand why this happens
    by looking at the agent construction and plugin list?

If not, simplify.

## 22. Production checklist

- [ ] Security decisions are deterministic.
- [ ] Trusted identity does not come from user text.
- [ ] High-risk tools can be cancelled/approved.
- [ ] Hook order is explicit where it matters.
- [ ] Retries are idempotency-aware.
- [ ] Hook logs are data-minimized.
- [ ] Hook latency/decisions are observable.
- [ ] Security hooks fail closed.
- [ ] Unit + integration tests cover policy behavior.

## Sources checked

- https://strandsagents.com/docs/user-guide/concepts/agents/hooks/
- https://strandsagents.com/docs/api/python/strands.hooks.events/
- https://strandsagents.com/docs/user-guide/sdk/interrupts/
- https://strandsagents.com/docs/user-guide/sdk/plugins/custom-plugins/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 08 — Agent Plugins & Skills](08-agent-plugins-skills.md). We will package reusable behavior and load domain instructions on demand without turning skills into an accidental permission system.

Back to the [course README](../README.md).
