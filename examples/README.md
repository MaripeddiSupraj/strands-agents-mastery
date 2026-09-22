# Runnable Examples

These are the hands-on labs for **Strands Agents Mastery**.

The lessons explain **why** a Strands feature exists. This directory shows **how to run it**.

Each lesson has a matching folder:

| Lesson | Example |
| --- | --- |
| 00 | [First Agent](00-what-is-strands-agents/) |
| 01 | [Core Components](01-core-components-deep-dive/) |
| 02 | [First Hands-On Agent](02-your-first-agent-hands-on/) |
| 03 | [Agent Loop + Limits](03-how-agents-really-work/) |
| 04 | [Model Providers](04-switching-model-providers/) |
| 05 | [MCP Tools](05-giving-your-agent-tools-via-mcp/) |
| 06 | [Streaming](06-callbacks-response-streaming/) |
| 07 | [Hooks](07-controlling-your-agent-with-hooks/) |
| 08 | [Skills](08-agent-plugins-skills/) |
| 09 | [Steering](09-improving-reliability-with-strands-steering/) |
| 10 | [Context Management](10-context-engineering-context-management/) |
| 11 | [Sessions](11-persistent-memory-with-session-managers/) |
| 12 | [Agents as Tools](12-multi-agent-patterns-agents-as-tools/) |
| 13 | [Graph](13-multi-agent-patterns-graph-workflows/) |
| 14 | [Swarm](14-multi-agent-patterns-agent-swarms/) |
| 15 | [A2A](15-agent2agent-a2a-talking-to-remote-agents/) |
| 16 | [Evals](16-evaluating-agents/) |
| 17 | [Observability](17-observability-traces-metrics-logs/) |
| 18 | [Security](18-security-guardrails-pii-redaction-responsible-ai/) |
| 19 | [AgentCore Deployment](19-deploying-agents-to-the-cloud/) |
| 20 | [Production Capstone](20-capstone-build-ship-production-multi-agent-system/) |

## How to use the labs

Create one virtual environment at the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install strands-agents
```

Then enter the example folder for the lesson and follow its README.

The default Python path uses Amazon Bedrock, so configure an AWS identity that can invoke the model you selected. Never put long-lived credentials in these example files.

Examples that need optional packages (MCP, A2A, Evals, AgentCore, provider extras) list the additional install command in their own README.

The examples intentionally grow one scenario: a **Payments API Incident Assistant**.
