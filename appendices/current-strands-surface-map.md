# Current Strands Surface Map

Last audited: **2026-09-23**

Strands evolves quickly. This appendix maps the major surfaces visible in the live documentation to this course and distinguishes deep production coverage from specialized or experimental material.

## Coverage matrix

| Current surface | Course coverage | Status |
| --- | --- | --- |
| Strands Harness vs Harness SDK | Lesson 01 + lab | Covered |
| Agent loop, limits, cancellation, retries | Lesson 03 | Deep |
| Tool executors | Lesson 03 + lab | Covered |
| Model providers | Lesson 04 | Deep |
| Model routing | Lesson 04 + lab | Covered |
| Custom/vended/community tools | Lessons 01–02 | Core coverage |
| MCP + transports/security | Lesson 05 | Deep |
| Structured output | Lesson 02 + lab | Covered |
| Standard streaming/callbacks/events | Lesson 06 | Deep |
| BidiAgent realtime | Lesson 06 + lab | Experimental |
| Hooks | Lesson 07 | Deep |
| Interventions | Lesson 07 + lab | Covered |
| Human-in-the-loop / interrupts | Lesson 07 | Production pattern |
| Cedar authorization | Lessons 07/18 + lab | Covered |
| Plugins / custom plugins | Lesson 08 | Core architecture |
| Skills | Lesson 08 | Deep |
| Context Offloader / Injector / GoalLoop | Lesson 08 + live docs | Specialized; reference only |
| Steering | Lesson 09 | Deep |
| Context management | Lesson 10 | Deep |
| Conversation / Agent / invocation state | Lesson 11 + lab | Covered |
| Sessions / snapshots / storage | Lesson 11 | Deep |
| Long-term MemoryManager | Lesson 11 + lab | Covered |
| Test memory store | Lesson 11 + lab | Learning backend |
| Bedrock Knowledge Base memory store | Lesson 11 | Production backend |
| Agents as Tools | Lesson 12 | Deep |
| Graph | Lesson 13 | Deep |
| Workflow | Lesson 13 + lab | Covered |
| Swarm | Lesson 14 | Deep |
| A2A | Lesson 15 | Deep |
| Evals | Lesson 16 | Deep |
| OpenTelemetry traces/metrics/logs | Lesson 17 | Deep |
| Guardrails / PII / Responsible AI | Lesson 18 | Deep |
| Trusted message history | Lesson 18 | Deep |
| Sandbox / Docker / SSH concepts | Lesson 18 + Docker lab | Covered |
| AgentCore Runtime | Lessons 19–20 | Deep |
| Lambda / Fargate / EKS | Lesson 19 | Deployment decisions |
| App Runner / EC2 / Docker / Kubernetes | Lesson 19 | Reference/decision coverage |
| Terraform | Lessons 19–20 | Deep |
| CI/CD / rollback | Lessons 19–20 | Deep |
| Experimental checkpoint/AgentConfig surfaces | Live reference | Experimental/reference only |

## What “complete” means here

The goal is mastery of the **major production engineering surfaces**, not one lesson per API-reference symbol, provider-specific flag, community integration, or experimental class.

Stable/current production primitives get explanation plus runnable labs. Specialized integrations are discoverable and linked. Experimental features are labeled explicitly.

## Canonical live sources

- https://strandsagents.com/docs/
- https://strandsagents.com/docs/user-guide/harness/
- https://strandsagents.com/docs/user-guide/sdk/
- https://github.com/strands-agents/harness-sdk
- https://github.com/strands-agents

If this appendix and the live docs disagree, the live docs are the source of truth and the course should be updated.
