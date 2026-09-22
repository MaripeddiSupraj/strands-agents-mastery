# Lesson 08 — Agent Plugins & Skills

Strands Agents Mastery → Phase 2 — Tools & Interaction

Plugins and Skills solve different problems.

A plugin changes or extends how an Agent behaves by composing SDK primitives such as hooks, tools, state, and prompt/context changes.

A Skill is a package of specialized instructions that an Agent can discover and activate on demand.

That distinction matters because an instruction package is not an authorization system.

## Map of this lesson

- Plugin mental model
- Current built-in plugin surfaces
- Custom plugins
- Skill progressive disclosure
- AgentSkills
- SKILL.md
- Resource files
- The allowed-tools security trap
- Runtime skill management
- Session persistence
- Supply-chain and testing concerns

## 1. Plugin versus Skill

Think of a plugin as executable extension behavior:

    Agent
      ↓
    Plugin
      ├── hooks
      ├── tools
      ├── state
      └── initialization/behavior

Think of a Skill as on-demand instruction/context:

    Agent sees skill metadata
      ↓
    decides skill is relevant
      ↓
    activates skill
      ↓
    receives detailed instructions/resources
      ↓
    uses already-available tools to do the work

A Skill does not automatically grant filesystem, shell, network, AWS, or MCP access.

Those capabilities still come from tools and runtime permissions.

## 2. Current plugin surface

Current Strands plugin documentation includes built-in/vended behaviors such as:

- Skills;
- Context Offloader;
- Context Injector;
- GoalLoop;
- Steering-related behavior.

Plugins modify the agent loop, so treat them like application dependencies, not static prompt files.

Review their:

- hook registrations;
- tool registrations;
- state changes;
- external I/O;
- model calls;
- data retention;
- version.

## 3. Attach a plugin

The current plugin API uses the Agent plugins list.

**Code sample — verified**

This example shape is from current Strands plugin documentation:

~~~python
from datetime import datetime, timezone

from strands import Agent
from strands.vended_plugins.context_injector import ContextInjector

agent = Agent(
    plugins=[
        ContextInjector(
            lambda context: (
                f"<now>{datetime.now(timezone.utc).isoformat()}</now>"
            )
        ),
    ],
)

agent("What time is it right now?")
~~~

The important architectural property is that the plugin runs as part of Agent behavior rather than relying on the model to remember to do something manually.

## 4. Custom plugins package related hooks

Current Strands exposes Plugin and the @hook decorator.

**Code sample — verified**

~~~python
from strands import Agent
from strands.plugins import Plugin, hook
from strands.hooks import BeforeToolCallEvent, AfterToolCallEvent

class LoggingPlugin(Plugin):
    name = "logging-plugin"

    @hook
    def log_before_tool(self, event: BeforeToolCallEvent) -> None:
        print(f"Calling: {event.tool_use['name']}")

    @hook
    def log_after_tool(self, event: AfterToolCallEvent) -> None:
        print(f"Completed: {event.tool_use['name']}")

agent = Agent(plugins=[LoggingPlugin()])
~~~

This is a better packaging boundary than copying the same two hooks into ten agent constructors.

## 5. What makes a good plugin

A production plugin should have:

- one clear responsibility;
- stable name;
- explicit configuration;
- deterministic failure behavior;
- bounded latency;
- observable decisions;
- unit tests;
- documented data access;
- documented tool/hook additions.

Avoid a “platform plugin” that secretly owns logging, authorization, retries, prompts, persistence, and network calls all at once.

## 6. Skills solve prompt bloat

Imagine one Agent supports:

- Terraform review;
- incident triage;
- Kubernetes debugging;
- release-note writing;
- SQL analysis.

A monolithic system prompt containing detailed instructions for all five domains wastes context and can create instruction interference.

Current AgentSkills uses progressive disclosure:

1. only skill name/description metadata is exposed initially;
2. the Agent activates a relevant skill;
3. full instructions and resource listing are then loaded.

This reduces always-on context.

## 7. Use AgentSkills

**Code sample — verified**

~~~python
from strands import Agent, AgentSkills, Skill

plugin = AgentSkills(skills="./skills/")

agent = Agent(plugins=[plugin])
~~~

The current API supports skill sources including filesystem locations, HTTPS sources, and programmatic Skill objects.

For a sensitive production system, do not allow uncontrolled remote skill URLs to become runtime instruction updates.

## 8. Programmatic Skill

**Code sample — verified**

~~~python
from strands import Skill

skill = Skill(
    name="code-review",
    description="Review code for best practices and bugs",
    instructions="Review the provided code. Check for...",
)
~~~

This is useful when skill content is generated or packaged through application configuration rather than a filesystem directory.

## 9. Parse skill content

Current Strands also supports Skill.from_content.

**Code sample — verified**

~~~python
from strands import Skill

skill = Skill.from_content(
    """---
name: code-review
description: Review code for best practices and bugs
---
Review the provided code. Check for...
"""
)
~~~

The exact content is just an example. In production, version the skill text and test changes the same way you test prompt changes.

## 10. SKILL.md format

Current Skills follow the Agent Skills specification.

A skill directory contains SKILL.md with YAML frontmatter followed by Markdown instructions.

**Code sample — verified**

The field structure below matches the current documented format:

~~~markdown
---
name: code-review
description: Review code for best practices and bugs
allowed-tools: file_editor shell
---

# Code review

Review the supplied code and report correctness, security,
maintainability, and test gaps.
~~~

The current documentation lists name and description as required fields.

## 11. Critical security point: allowed-tools is informational

At the time this lesson was verified, the current Strands documentation states that the Skills allowed-tools field is informational.

It is included in the instructions when a skill activates, but it does not enforce or restrict runtime tool access.

So this:

    allowed-tools: read_file

does not mean:

    shell is technically unavailable

if shell was already registered on the Agent.

Do not build authorization around allowed-tools.

Runtime capability comes from the Agent’s actual registered tools and their authorization.

## 12. Resource directories

Current Skill packaging supports conventional resource directories:

    my-skill/
      SKILL.md
      scripts/
      references/
      assets/

When activated, the AgentSkills response can list resource files.

But the plugin does not automatically read or execute those files.

The Agent needs appropriate tools to access them.

That separation is good security architecture.

## 13. Resource access must be explicit

Current docs show filesystem Skills paired with vended file_editor and shell tools.

**Code sample — verified**

~~~python
from strands import Agent, AgentSkills
from strands.vended_tools import file_editor, shell

plugin = AgentSkills(skills="./skills/")

agent = Agent(
    plugins=[plugin],
    tools=[file_editor, shell],
)
~~~

This is a useful development example.

For production, pause before copying it.

A shell tool can have enormous capability. Prefer:

- sandboxed execution;
- narrow purpose-built tools;
- read-only filesystem mounts;
- constrained working directories;
- no ambient production credentials;
- network egress controls.

## 14. Skills are a supply-chain input

A Skill can tell the model what steps to follow.

If an attacker can modify SKILL.md, they may influence how the Agent uses its legitimate tools.

Treat skills like code/configuration:

- source review;
- repository ownership;
- protected branches;
- signed/reproducible artifact path where required;
- pin versions;
- audit changes;
- do not fetch arbitrary mutable URLs in a sensitive runtime.

A remote HTTPS Skill is convenient, but convenience is not provenance.

## 15. Scripts inside a Skill are executable artifacts

A script in skills/foo/scripts is not safe because it lives under a directory named “skills.”

If your Agent has shell execution and the Skill tells it to run the script, that script executes with the shell tool’s environment.

Review it like any other executable dependency.

## 16. Use strict validation in controlled builds

Current AgentSkills exposes a strict parameter. When strict=False, validation issues may produce warnings; strict=True raises errors for validation problems.

For a CI/build pipeline, strict validation is usually preferable because malformed skill metadata should fail before production.

Use current API documentation for all validation behavior when upgrading SDK versions.

## 17. Runtime skill inspection

Current Python API exposes methods to inspect and update available skills.

**Code sample — verified**

~~~python
from strands import Agent, AgentSkills, Skill

plugin = AgentSkills(skills="./skills/pdf-processing")
agent = Agent(plugins=[plugin])

for skill in plugin.get_available_skills():
    print(f"{skill.name}: {skill.description}")

new_skill = Skill(
    name="summarize",
    description="Summarize long documents",
    instructions="Read the document and produce a concise summary...",
)

plugin.set_available_skills(
    plugin.get_available_skills() + [new_skill]
)

activated = plugin.get_activated_skills(agent)
print(f"Activated skills: {activated}")
~~~

Dynamic mutation can be useful, but production systems should define who is authorized to change the available skill set.

## 18. Skill state and sessions

Current AgentSkills tracks activated skills in Agent state under a configurable state key.

That state can participate in session persistence.

This has a subtle consequence:

    skill activated in earlier interaction
      ↓
    session persists
      ↓
    later invocation may retain skill activation state

Test session-resume behavior when skill availability changes across releases.

Do not assume an old session automatically behaves exactly like a new deployment.

## 19. Context cost tradeoff

Skills save always-on system prompt tokens, but activation itself requires a tool-style interaction and adds instructions into working context.

Use Skills when:

- instructions are domain-specific;
- many skills exist;
- most requests need only a small subset.

Do not split a five-line universal policy into a Skill just to say you use Skills. Always-relevant policy belongs in the always-relevant control layer.

## 20. Skills versus multi-agent

Use a Skill when:

    same Agent role/model/tools
    + different specialized instructions

Use a specialist Agent when:

    different role
    different model
    different tools/permissions
    different context isolation
    or independent deployment

Multi-agent systems cost more operationally. Do not create an Agent per instruction file.

## 21. Skills versus Steering

Skill:

    “Here is the detailed procedure for Kubernetes incident analysis.”

Steering:

    “Given what has happened so far, this next tool call should be redirected/confirmed.”

Skills are knowledge/procedure modules.

Steering is context-sensitive guidance/control during execution.

Lesson 09 makes this distinction concrete.

## 22. Observability

Track safe skill/plugin events:

- plugin initialization success/failure;
- available skill count/version;
- skill activation;
- activation latency;
- tool calls after activation;
- task quality/cost before versus after skill changes.

Do not log full private skill content if the skill itself contains confidential procedures.

## 23. Testing a Skill

A good Skill test set includes:

### Discovery

Does the Agent recognize when the Skill is relevant?

### Non-activation

Does it avoid loading the Skill for unrelated tasks?

### Procedure adherence

Does it follow required steps after activation?

### Security

Does malicious input override the Skill’s safety constraints?

Does the Skill attempt tools it should not have?

### Resource behavior

Are referenced files/scripts present and versioned?

### Regression

Does a Skill text update improve the target cases without harming unrelated ones?

## 24. Production checklist

- [ ] Plugins have one clear responsibility.
- [ ] Plugin hook/tool additions are documented.
- [ ] Skill source is trusted and versioned.
- [ ] strict validation is considered in CI.
- [ ] allowed-tools is not mistaken for authorization.
- [ ] Executable resource scripts are reviewed.
- [ ] Shell/filesystem access is sandboxed or minimized.
- [ ] Skill state/session behavior is tested.
- [ ] Skill activation is observable.
- [ ] Skill changes run through behavioral evaluation.

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/plugins/
- https://strandsagents.com/docs/user-guide/sdk/plugins/custom-plugins/
- https://strandsagents.com/docs/user-guide/sdk/plugins/skills/
- https://strandsagents.com/docs/api/python/strands.vended_plugins.skills.agent_skills/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 09 — Improving Reliability with Strands Steering](09-improving-reliability-with-strands-steering.md). We will add context-sensitive guidance around model/tool behavior while keeping hard authorization in deterministic controls.

Back to the [course README](../README.md).
