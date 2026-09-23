# Example 19 — Deploying Agents to AgentCore

## Goal

Wrap the same Strands Agent in the current Bedrock AgentCore Runtime application adapter.

## Install

```bash
pip install strands-agents bedrock-agentcore
npm install -g @aws/agentcore
```

## Local/deploy flow

```bash
agentcore create
agentcore dev
agentcore deploy
agentcore invoke
```

Read Lesson 19 before deploying. Use a separate least-privilege runtime role and deployment role. Do not put access keys in `app.py`.
