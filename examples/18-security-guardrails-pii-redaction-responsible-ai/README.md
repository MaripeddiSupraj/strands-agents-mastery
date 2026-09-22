# Example 18 — Security, Guardrails & PII

## Goal

Attack the incident assistant deliberately and verify that executable capability remains bounded.

## Run

```bash
pip install strands-agents
python main.py
```

The example focuses on deterministic tool policy. Configure Bedrock Guardrails/PII controls from Lesson 18 for your AWS account and then rerun the same red-team prompts.

Security success is not “the model politely refused.” Verify the dangerous tool never executes and runtime IAM also denies unauthorized writes.
