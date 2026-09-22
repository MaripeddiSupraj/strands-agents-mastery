# Strands Agents Mastery

A hands-on, enterprise-grade learning path for the AWS Strands Agents SDK, from the first agent loop to a production multi-agent deployment.

This repository is Python-first. TypeScript differences are called out where the current official documentation exposes a materially different API or behavior.

## Documentation freshness

The course is maintained against the live Strands documentation and source. The current revision was re-verified on **2026-09-22** against:

- https://strandsagents.com/docs/
- https://github.com/strands-agents/harness-sdk
- https://github.com/strands-agents

Strands evolves quickly. Every lesson distinguishes code copied or directly matched to official documentation as **verified** from examples that are intentionally course-authored as **illustrative**.

## How to use this course

Do the lessons in order. Do not rush to multi-agent orchestration before you can explain a single agent loop, tool execution, context pressure, and failure behavior.

For each lesson:

1. Read the mental model first.
2. Run the smallest verified example.
3. Change one thing and observe the trace.
4. Complete the production checklist.
5. Add at least one test before moving on.

## The running hands-on example

This course does not use a completely unrelated demo in every lesson.

From Lesson 00 onward, the recommended labs grow one system: a **Payments API Incident Assistant**. Every lesson begins with a clearly marked **Recommended hands-on example** that tells you what to build, what to run, what to observe, and why that example matters.

| Lesson | Recommended example progression |
| --- | --- |
| 00 | One Agent + one safe `get_service_status` tool |
| 01 | Map every Strands component onto the future incident assistant |
| 02 | Build the first working payments-api status assistant |
| 03 | Trace the complete model → tool → model loop and its budgets |
| 04 | Run the same incident task on different model providers |
| 05 | Add authoritative AWS documentation through MCP |
| 06 | Stream a live incident investigation safely |
| 07 | Block an attempted production restart with a deterministic hook |
| 08 | Package the incident-response procedure as a Skill |
| 09 | Use Steering to improve a wasteful/failed investigation path |
| 10 | Control context growth from long logs and tool results |
| 11 | Resume the same incident after process restart |
| 12 | Split the assistant into Incident Commander + specialist Agents |
| 13 | Express the investigation as a controlled Graph |
| 14 | Compare a Swarm and measure autonomous handoff cost/behavior |
| 15 | Move one specialist behind an A2A service boundary |
| 16 | Turn incident scenarios into a repeatable evaluation suite |
| 17 | Trace one slow incident end to end and explain the latency |
| 18 | Red-team prompt injection, tool-output injection, PII, and IAM |
| 19 | Deploy the same assistant to AgentCore instead of starting a new demo |
| 20 | Build, test, deploy, observe, and roll back the complete production system |

The recommendation is simple: **run the highlighted example first, then read the deeper sections.** The theory will make more sense because you already know which concrete problem it is explaining.

## Roadmap

### Phase 1 — Core Agent Mechanics

- 🟢 [00 — What Is Strands Agents?](lessons/00-what-is-strands-agents.md)
- 🟢 [01 — Core Components Deep Dive](lessons/01-core-components-deep-dive.md)
- 🟢 [02 — Your First Agent, Hands-On](lessons/02-your-first-agent-hands-on.md)
- 🟢 [03 — How Agents Really Work](lessons/03-how-agents-really-work.md)
- 🟢 [04 — Switching Model Providers](lessons/04-switching-model-providers.md)

### Phase 2 — Tools & Interaction

- 🟢 [05 — Giving Your Agent Tools via MCP](lessons/05-giving-your-agent-tools-via-mcp.md)
- 🟢 [06 — Callbacks & Response Streaming](lessons/06-callbacks-response-streaming.md)
- 🟢 [07 — Controlling Your Agent With Hooks](lessons/07-controlling-your-agent-with-hooks.md)
- 🟢 [08 — Agent Plugins & Skills](lessons/08-agent-plugins-skills.md)
- 🟢 [09 — Improving Reliability with Strands Steering](lessons/09-improving-reliability-with-strands-steering.md)

### Phase 3 — Memory & Context

- 🟢 [10 — Context Engineering & Context Management](lessons/10-context-engineering-context-management.md)
- 🟢 [11 — Persistent Memory with Session Managers](lessons/11-persistent-memory-with-session-managers.md)

### Phase 4 — Multi-Agent Systems

- 🟢 [12 — Multi-Agent Patterns: Agents as Tools](lessons/12-multi-agent-patterns-agents-as-tools.md)
- 🟢 [13 — Multi-Agent Patterns: Graph Workflows](lessons/13-multi-agent-patterns-graph-workflows.md)
- 🟢 [14 — Multi-Agent Patterns: Agent Swarms](lessons/14-multi-agent-patterns-agent-swarms.md)
- 🟢 [15 — Agent2Agent (A2A): Talking to Remote Agents](lessons/15-agent2agent-a2a-talking-to-remote-agents.md)

### Phase 5 — Production Readiness

- 🟢 [16 — Evaluating Agents](lessons/16-evaluating-agents.md)
- 🟢 [17 — Observability: Traces, Metrics & Logs](lessons/17-observability-traces-metrics-logs.md)
- 🟢 [18 — Security: Guardrails, PII Redaction & Responsible AI](lessons/18-security-guardrails-pii-redaction-responsible-ai.md)
- 🟢 [19 — Deploying Agents to the Cloud](lessons/19-deploying-agents-to-the-cloud.md)

### Phase 6 — Capstone

- 🟢 [20 — Capstone: Build & Ship a Production Multi-Agent System](lessons/20-capstone-build-ship-production-multi-agent-system.md)

## Course standard

A lesson is not complete merely because its happy-path sample runs. The course treats the following as part of agent engineering from the beginning:

- bounded execution and retry behavior;
- model and tool cost visibility;
- least-privilege credentials;
- prompt injection and untrusted tool-output handling;
- PII and sensitive-data handling;
- traces, metrics, and structured logs;
- deterministic tests plus behavioral evaluation;
- reproducible packaging, CI/CD, and infrastructure as code.

## Repository note

This is a community learning repository. Verify service quotas, model availability, pricing, IAM actions, and regional availability in your own AWS account before deploying production workloads.
