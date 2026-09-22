# Lesson 04 — Switching Model Providers

Strands Agents Mastery → Phase 1 — Core Agent Mechanics

Strands is model-provider agnostic, but “the code still runs” is not the same as “the system still behaves correctly.”

Changing a model can change tool selection, latency, cost, structured-output quality, context limits, privacy posture, regional availability, and retry behavior. This lesson teaches provider switching as an engineering decision rather than an import statement.

## Map of this lesson

- The provider abstraction
- Amazon Bedrock
- Anthropic
- OpenAI
- Ollama
- Other documented providers
- Configuration and secrets
- Capability differences
- Cost/latency tradeoffs
- Fallback and routing cautions
- A provider evaluation matrix
- Testing a provider migration

## 1. The stable part of the application

At a high level:

    Agent
      ↓
    Model interface
      ↓
    provider implementation
      ↓
    Bedrock / Anthropic / OpenAI / Ollama / ...

The goal is that your tools, hooks, sessions, and orchestration do not need to be rewritten merely because the provider changes.

But your evaluation suite must be rerun.

## 2. Install only the provider extras you need

**Code sample — verified**

Current model-provider documentation shows provider-specific extras:

~~~bash
pip install 'strands-agents[bedrock]'
pip install 'strands-agents[openai]'
pip install 'strands-agents[anthropic]'
~~~

It also documents:

**Code sample — verified**

~~~bash
pip install 'strands-agents[all]'
~~~

For local experimentation, all may be convenient.

For production images, provider-specific dependencies are usually better:

- smaller image;
- fewer transitive packages;
- smaller dependency attack surface;
- clearer SBOM;
- easier vulnerability triage.

Pin versions through your normal dependency-management process.

## 3. Amazon Bedrock: the default Python path

Current Strands quickstart documentation uses Amazon Bedrock as the default provider, so no explicit model object is required for the simplest case.

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent()
print(agent("What can you help me build?"))
~~~

The live quickstart currently documents Claude Sonnet 4.6 as the default Bedrock model configuration in the default region used by the SDK quickstart. Treat defaults as convenience, not permanent production configuration: pin the model/region behavior you require rather than assuming a default will never change.

## 4. Bedrock authentication and IAM

For local development, Strands uses the normal AWS credential chain/service behavior.

For deployed workloads, prefer workload identity:

- Lambda execution role;
- ECS task role;
- EKS Pod Identity/IRSA-style workload role as appropriate;
- AgentCore runtime role.

Avoid embedding AWS access keys in environment files committed to Git.

The current Bedrock model documentation calls out model invocation permissions such as bedrock:InvokeModelWithResponseStream for streaming access. Exact resource scoping depends on the model/inference profile and region.

Start from deny-by-default and grant only the actions/resources the runtime actually needs.

## 5. Explicit Bedrock model object

When you need provider-specific configuration, create BedrockModel rather than relying only on defaults.

The exact constructor surface evolves. Use the current BedrockModel reference for production configuration such as model ID, region/client configuration, guardrails, and service tier.

The verified provider-switching point remains:

**Code sample — verified**

~~~python
from strands import Agent
from strands.models.bedrock import BedrockModel

model = BedrockModel()
agent = Agent(model=model)
~~~

Do not invent constructor parameters from an old blog post; check the current BedrockModel API reference when setting advanced options.

## 6. Anthropic direct

Current Strands provider documentation supports Anthropic as an optional provider.

**Code sample — verified**

~~~python
from strands.models.anthropic import AnthropicModel

model = AnthropicModel(
    client_args={"api_key": "<KEY>"},
    max_tokens=1028,
    model_id="claude-sonnet-5",
    params={"temperature": 0.7},
)
~~~

Then attach it to the same Agent:

**Code sample — verified**

~~~python
from strands import Agent

agent = Agent(model=model)
~~~

For real code, do not hard-code the key literal. The current quickstart also documents reading ANTHROPIC_API_KEY from the environment when client configuration is omitted appropriately.

Store secrets in your platform’s secret manager and inject them at runtime.

## 7. OpenAI

Current Strands OpenAI provider documentation uses OpenAIModel.

**Code sample — verified**

~~~python
from strands.models.openai import OpenAIModel

model = OpenAIModel(
    client_args={"api_key": "<KEY>"},
    model_id="gpt-4o",
    params={
        "max_tokens": 1000,
        "temperature": 0.7,
    },
)
~~~

The current quickstart also shows environment-based OPENAI_API_KEY configuration and newer model IDs. Model names change faster than the SDK concepts, so keep them in configuration rather than scattering them through application code.

## 8. Ollama for local models

Ollama is useful when you want a local development path without a cloud API key.

**Code sample — verified**

~~~bash
pip install 'strands-agents[ollama]'

ollama serve
ollama pull llama3.1
~~~

**Code sample — verified**

~~~python
from strands import Agent
from strands.models.ollama import OllamaModel

model = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.1",
)

agent = Agent(model=model)
agent("What is an agent harness, in one sentence?")
~~~

Local does not automatically mean production-ready.

You still need to evaluate:

- model quality;
- hardware memory;
- concurrency;
- cold/warm behavior;
- model download/supply chain;
- patching;
- network exposure of the Ollama endpoint;
- GPU/CPU utilization;
- observability.

## 9. “And beyond”

The current Strands model-provider docs list additional provider integrations including options such as Google, LiteLLM, Mistral, SageMaker, Llama API, llama.cpp, Writer, and OpenAI-compatible routes.

Do not copy a constructor from this lesson for those providers unless the live provider page verifies it. The exact installation extras and configuration vary.

The architectural pattern is still:

    configure provider-specific Model
      ↓
    pass model to Agent
      ↓
    keep agent/tool/session code stable
      ↓
    rerun evaluations

## 10. Capability parity is not guaranteed

Before a provider migration, make a capability table.

Typical dimensions:

| Capability | Why it matters |
| --- | --- |
| Tool calling | Can the agent act reliably? |
| Streaming | Can the UI show progressive output? |
| Structured output | Can downstream code trust the response schema? |
| Context window | How much history/tool data fits? |
| Prompt caching | Can repeated context be cheaper/faster? |
| Multimodal input | Do image/audio workflows still work? |
| Guardrails/safety integration | Does your existing control layer still apply? |
| Regional hosting | Does it meet residency/compliance needs? |
| Throughput/quota | Can it meet peak traffic? |

Use the current provider capability table because these features change.

## 11. Behavioral parity matters more than API parity

Imagine two models both support tools.

Model A:

    chooses incident_lookup correctly 98% of the time

Model B:

    chooses broad_log_search frequently,
    even when incident_lookup is enough

The Python code is compatible. The operational cost is not.

Provider migration therefore requires replaying representative tasks and measuring:

- tool selection;
- tool arguments;
- number of turns;
- total tokens;
- latency;
- goal success;
- refusal/policy behavior;
- hallucination after tool errors.

Lesson 16 gives you the evaluation machinery.

## 12. Centralize model configuration

Avoid this anti-pattern:

    agent_a.py → hard-coded model X
    agent_b.py → hard-coded model X
    agent_c.py → hard-coded model Y by mistake

A configuration boundary is easier to audit.

**Code sample — illustrative**

~~~python
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class ModelSettings:
    provider: str
    model_id: str

def load_model_settings() -> ModelSettings:
    provider = os.environ.get("MODEL_PROVIDER", "bedrock")
    model_id = os.environ["MODEL_ID"]

    if provider not in {"bedrock", "anthropic", "openai", "ollama"}:
        raise ValueError(f"Unsupported provider: {provider}")

    return ModelSettings(provider=provider, model_id=model_id)
~~~

The factory that turns this into provider objects should use the exact current constructors for your pinned Strands version.

## 13. Secrets and configuration are different

Configuration:

- model ID;
- region;
- max tokens;
- temperature;
- service tier.

Secrets:

- API key;
- bearer token;
- private endpoint credential.

Do not put both into one plaintext config file just because both are “settings.”

For AWS-native workloads, prefer IAM identity where possible. For external providers, use your runtime secret store and rotate keys.

## 14. Bedrock service tier is a cost/latency knob

Current BedrockModel source/docs expose service-tier options including default, priority, and flex where supported by Bedrock.

That means model choice is not your only latency/cost lever.

Treat tier selection as an SLO decision:

- interactive user request may value latency;
- asynchronous batch enrichment may value cost;
- failover traffic may need explicit policy.

Availability and pricing are AWS-service concerns and can change. Verify them in current Bedrock documentation before production rollout.

## 15. Model max tokens versus invocation token budget

Do not confuse:

    model max_tokens

with:

    agent invocation limits.total_tokens / output_tokens

The model’s output cap controls one generation.

Invocation limits bound the repeated agent loop across turns.

A sane production design uses both.

## 16. Cost model for an agent invocation

A simplified view:

    total model cost
      ≈ Σ(all model calls in all turns)
        input tokens + output tokens
        adjusted for provider pricing/caching

Then add:

- external tool API cost;
- vector/database queries;
- logs/traces;
- network;
- compute.

A “cheaper per-token” model can cost more overall if it needs more turns or calls the wrong tools.

Measure the whole task.

## 17. Latency model

Likewise:

    total latency
      ≈ model latency
      + tool latency
      + retry backoff
      + extra turns
      + orchestration overhead

A faster model that repeatedly misroutes tools may produce a slower application.

## 18. Do not build naive fallback routing

It is tempting to write:

    if provider A fails:
        use provider B

But ask:

- Does provider B support the same tools?
- Will the context format work?
- Is the data allowed to leave provider A’s environment?
- Does provider B meet regional policy?
- Are guardrails equivalent?
- Does retrying create duplicate side effects?
- Do you have evaluation evidence for B?

Cross-provider fallback is an architecture change, not just exception handling.

## 19. Provider evaluation harness

Before promoting a new model/provider, run the same dataset through both.

Suggested dataset categories:

- no-tool questions;
- single-tool lookups;
- ambiguous tool choice;
- multi-tool task;
- invalid tool argument;
- downstream tool failure;
- prompt-injection attempt in tool output;
- large-context case;
- policy-sensitive input;
- structured-output case.

Capture:

- pass/fail;
- tool trajectory;
- tokens;
- duration;
- stop reason;
- policy outcome.

Do not pick the “winner” from five hand-written prompts.

## 20. Observability when switching models

Attach provider/model identity as safe trace attributes or structured-log fields.

At minimum, your operational view should separate:

- provider;
- model ID;
- environment;
- agent version;
- request/session correlation ID.

Then a regression after deployment can be correlated with a model change instead of becoming “the agent got worse.”

Avoid putting secrets or user content into metric labels.

## 21. IAM and network differences

Bedrock:

- AWS IAM;
- AWS regional endpoint;
- VPC/network architecture depending on your environment.

External provider:

- API secret/token;
- internet or controlled egress;
- different audit path;
- potentially different data residency.

Local Ollama:

- local/network service identity;
- host/container security;
- model artifact provenance;
- compute isolation.

The provider abstraction hides model-call syntax. It does not erase infrastructure differences.

## 22. CI/CD gate for a provider change

A model/provider PR should not be “MODEL_ID changed.”

A stronger gate is:

1. dependency scan passes;
2. unit tests pass;
3. integration smoke test passes;
4. fixed eval set runs;
5. quality threshold meets baseline;
6. token/latency budget is within allowed regression;
7. security/policy cases pass;
8. deployment environment has required credentials/IAM;
9. canary rollout observes real metrics before broad promotion.

Store the evaluated model configuration with the artifact/release.

## 23. Exercise: controlled provider comparison

Pick one read-only tool agent.

Run 20–50 representative prompts on two providers.

Record:

- correct tool selection;
- argument correctness;
- turns;
- total tokens;
- end-to-end latency;
- final goal success.

Then explain why one configuration better fits your SLO.

Do not judge from prose style alone.

## 24. Production rules from this lesson

1. Provider compatibility is not behavioral parity.
2. Pin model configuration explicitly for production.
3. Keep secrets out of source and plain config.
4. Use least-privilege workload identity for AWS.
5. Evaluate provider changes against representative trajectories.
6. Measure whole-task cost, not token price alone.
7. Treat fallback routing as a security/compliance decision.
8. Keep provider/model identity observable.

## Sources checked

- https://strandsagents.com/docs/user-guide/concepts/model-providers/
- https://strandsagents.com/docs/user-guide/sdk/quickstart/python/
- https://strandsagents.com/docs/user-guide/sdk/quickstart/overview/
- https://strandsagents.com/docs/user-guide/concepts/model-providers/amazon-bedrock/
- https://strandsagents.com/docs/user-guide/concepts/model-providers/anthropic/
- https://strandsagents.com/docs/user-guide/concepts/model-providers/openai/
- https://strandsagents.com/docs/user-guide/concepts/model-providers/ollama/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 05 — Giving Your Agent Tools via MCP](05-giving-your-agent-tools-via-mcp.md). We will connect external tool servers through Model Context Protocol without turning the agent runtime into an unrestricted remote-control process.

Back to the [course README](../README.md).
