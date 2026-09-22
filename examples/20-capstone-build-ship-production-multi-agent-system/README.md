# Example 20 — Production Multi-Agent Capstone

## Goal

Assemble the course into a read-only AWS Incident Triage Copilot.

This folder is intentionally larger than the earlier labs.

## Install

```bash
pip install strands-agents bedrock-agentcore
```

For the real MCP-backed version, also make `uvx` available and run the pinned AWS Labs CloudWatch and AWS Documentation MCP packages described in Lesson 20.

## Files

- `local.py` — locally runnable multi-agent version with deterministic synthetic tools.
- `app.py` — AgentCore host adapter around the same core Agent.
- `infra/main.tf` — current Terraform AgentCore runtime/endpoint resource shapes.

## Recommended progression

1. Run `python local.py`.
2. Replace synthetic specialist tools with the real MCP clients from Lesson 20 in a test AWS account.
3. Add persistent sessions and guardrails.
4. Run the eval/security dataset.
5. Build an immutable image.
6. Deploy through Terraform/CI.
7. Run the post-deploy synthetic incident and inspect traces + CloudTrail.
