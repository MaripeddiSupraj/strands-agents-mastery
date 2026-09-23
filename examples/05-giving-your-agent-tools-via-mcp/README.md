# Example 05 — Giving Your Agent Tools via MCP

## Goal

Connect the Agent to the AWS Documentation MCP server instead of implementing the documentation integration inside the Agent process.

## Prerequisites

Install Strands and ensure `uvx` is available.

```bash
pip install strands-agents
python main.py
```

The example launches `awslabs.aws-documentation-mcp-server@latest` exactly like the current Strands MCP example. For a real release, pin the MCP server version you tested.

Observe tool discovery/calls and remember: MCP tool output is still untrusted data.
