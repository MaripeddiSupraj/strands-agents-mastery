# Lesson 19 — Deploying Agents to the Cloud

Strands Agents Mastery → Phase 5 — Production Readiness

A Strands Agent is a library object running inside your process.

Deployment is therefore not “upload the Agent to Strands.”

You package the application that owns the Agent and run it on a compute target.

Current Strands documentation covers targets including:

- Amazon Bedrock AgentCore Runtime;
- AWS Lambda;
- AWS Fargate;
- AWS App Runner;
- Amazon EKS;
- Amazon EC2;
- Docker;
- Kubernetes.

This lesson focuses on the four targets most useful for the course:

    Lambda
    Fargate
    EKS
    AgentCore Runtime

The capstone uses AgentCore Runtime.

## Map of this lesson

- What actually changes at deployment
- A deploy-ready HTTP Agent
- Containers
- Lambda
- Fargate
- EKS
- AgentCore Runtime
- Current AgentCore Python wrapper
- Current AgentCore CLI
- IAM
- Networking
- Session/state
- Observability
- Scaling and concurrency
- Terraform
- CI/CD
- Image scanning and supply chain
- Rollback
- Choosing a target


## Recommended hands-on example — Deploy the same incident assistant, not a new hello-world Agent

> **Build today:** Package the payments-api incident assistant you already understand and deploy it to the current AgentCore Runtime path.
>
> **Local proof:** run the core Agent without the cloud host adapter.
>
> **Deployment proof:** build one immutable artifact, deploy it with a least-privilege runtime role, invoke it through the deployed endpoint, and run a harmless incident prompt.
>
> **Verify:** runtime identity, endpoint response, session behavior, traces, token/tool metrics, MCP connectivity, and a post-deploy synthetic check.
>
> **Why this example:** learners see what deployment actually changes: packaging, identity, networking, state, scaling, and operations. The Strands reasoning code should not be rewritten just because the compute target changed.

Do not count “Terraform apply succeeded” or “agentcore deploy returned success” as the final test. Invoke the real service path.


## 1. The Agent does not need to be rewritten for every host

The same core Agent can sit behind different entry points.

Conceptually:

    core Agent code
       ↓
    host adapter
       ├── Lambda handler
       ├── FastAPI container
       └── AgentCore app entrypoint

Keep business/Agent construction separate from host-specific HTTP/server code.

That makes deployment targets replaceable and testable.

## 2. A common HTTP shape

Current Strands deployment documentation uses an HTTP pattern with:

- POST /invocations;
- GET /ping.

**Code sample — verified**

~~~python
from fastapi import FastAPI
from strands import Agent

app = FastAPI()
agent = Agent()

@app.post("/invocations")
async def invoke(request: dict):
    result = agent(request["prompt"])
    return {"output": result.message}

@app.get("/ping")
def ping():
    return {"status": "healthy"}
~~~

This is intentionally small.

A production endpoint still needs:

- authentication;
- request schema;
- request size limit;
- session authorization;
- timeout/cancellation;
- error mapping;
- telemetry;
- rate limiting;
- streaming design if needed.

## 3. Define Agent ownership before you scale

A stateful Agent instance owns mutable conversation state.

For a web service choose one design deliberately:

### Stateless request

Each request gets isolated conversation state.

### Session-scoped Agent

Restore state using an authenticated and authorized session identity.

### Per-context remote Agent

For A2A, use the current agent_factory pattern so contexts do not share one Agent instance.

Do not route unrelated users into one global conversation object.

## 4. Container is the portable baseline

Fargate, EKS, AgentCore custom-container deployments, and generic Kubernetes all benefit from a reproducible container.

A production image should:

- run as non-root;
- contain only needed provider extras/tools;
- pin dependencies;
- use a small approved base;
- include health behavior;
- contain no live credentials;
- be scanned;
- have an SBOM;
- be immutable after build.

Build once and promote the same artifact across environments where possible.

## 5. Keep secrets out of the image

Bad:

    COPY .env /app/.env

Better:

- IAM workload identity for AWS access;
- Secrets Manager or an approved secret store for external provider keys;
- AgentCore Identity or the platform's supported identity mechanism where applicable.

The image should be safe to store in ECR without embedding production credentials.

## 6. Lambda: good for bounded, short-lived invocations

Current Strands Lambda guidance positions Lambda for short-lived Agent invocations.

Advantages:

- no hosts to manage;
- event-driven scale;
- pay for execution;
- natural API/event integration.

Considerations:

- execution duration limits;
- cold start;
- package/layer size;
- externalized session state;
- downstream connection behavior.

The current Strands Lambda tutorial does not implement response streaming and explicitly points to Fargate when the tutorial's streaming requirement matters.

## 7. Lambda IAM

Use a dedicated execution role.

Typical capability categories:

- exact Bedrock model invocation;
- CloudWatch Logs;
- exact session storage prefix/table;
- exact business AWS APIs required by tools.

Do not attach AdministratorAccess to make an Agent demo work.

If a tool only needs to read one bucket prefix, scope the role to that prefix where IAM supports it.

## 8. Lambda is not ideal for every Agent

Avoid forcing Lambda when the Agent:

- streams for a long time;
- performs long multi-agent orchestration;
- needs stable long-lived connections;
- has heavy per-request initialization;
- needs a container/service operational model.

A managed container runtime may be simpler.

## 9. Fargate: managed containers without worker-node management

Current Strands Fargate documentation uses a containerized FastAPI Agent and positions Fargate for workloads needing streaming, concurrency, or high availability.

Fargate is useful when you want:

- Docker packaging;
- ECS service/task controls;
- task IAM roles;
- VPC networking;
- load balancing;
- autoscaling

without operating EC2 worker nodes.

## 10. Separate Fargate deployment identity from runtime identity

### CI/deployment role

Can build/push and update approved infrastructure.

### ECS task role

Can invoke the model and access only runtime dependencies.

Do not let the running Agent inherit the same broad role used by CI to modify its own infrastructure.

This separation reduces blast radius if the Agent process is compromised.

## 11. Fargate networking

A common shape is:

    ingress / API layer
       ↓
    load balancer
       ↓
    private ECS tasks
       ↓
    Bedrock / MCP / internal APIs

Consider:

- private subnets;
- VPC endpoints where useful;
- security groups;
- controlled egress;
- TLS;
- WAF/rate limiting for public ingress.

Network egress is an Agent security control because tools can send data.

## 12. EKS: choose Kubernetes when you need Kubernetes

Current Strands EKS tutorial uses a containerized FastAPI Agent and demonstrates EKS Auto Mode.

EKS is a strong fit when your platform already depends on:

- Kubernetes policy;
- service mesh;
- custom scheduling;
- advanced rollout controls;
- network policy;
- shared platform services;
- GPU/specialized compute;
- many related workloads.

Do not choose EKS only because it sounds more enterprise.

It adds operational surface for a simple Agent service.

## 13. EKS workload identity

Do not put long-lived AWS access keys into Kubernetes Secrets for normal AWS service access.

Use the current AWS-supported EKS workload identity mechanism for your environment and scope the role to the pod/workload.

Also apply:

- namespace isolation;
- NetworkPolicy where supported;
- Pod Security controls;
- CPU/memory limits;
- image admission/policy;
- secrets integration;
- autoscaling.

Application authorization is still required.

## 14. AgentCore Runtime: purpose-built managed Agent runtime

Current Strands documentation describes Amazon Bedrock AgentCore Runtime as a serverless runtime purpose-built for Agent workloads.

Current documented capabilities include:

- Strands and other frameworks;
- MCP and A2A;
- multiple model providers;
- long-running, real-time, and multimodal Agents;
- dedicated microVM isolation per user session;
- session persistence;
- fast scale-out;
- integration with AgentCore Identity.

This removes much of the generic container orchestration work when the workload fits AgentCore.

## 15. Session microVM isolation is not authorization

Per-session microVM isolation helps separate runtime state.

It does not automatically provide:

- caller authentication;
- tool authorization;
- least-privilege IAM;
- PII classification;
- business approval.

The controls from Lesson 18 still apply.

## 16. Current Python AgentCore SDK wrapper

Current Strands AgentCore deployment guidance uses the bedrock-agentcore package.

**Code sample — verified**

~~~bash
pip install bedrock-agentcore
~~~

**Code sample — verified**

~~~python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()
agent = Agent()

@app.entrypoint
def invoke(payload):
    """Process user input and return a response."""
    user_message = payload.get("prompt", "Hello")
    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
~~~

The wrapper supplies the runtime-facing application behavior while the Strands Agent remains normal Agent code.

## 17. Current AgentCore streaming wrapper

The current deployment guide also demonstrates an async streaming entrypoint.

**Code sample — verified**

~~~python
from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
agent = Agent()

@app.entrypoint
async def agent_invocation(payload):
    user_message = payload.get(
        "prompt",
        "No prompt found in input.",
    )

    stream = agent.stream_async(user_message)

    async for event in stream:
        yield event

if __name__ == "__main__":
    app.run()
~~~

For a real product, apply Lesson 06 filtering so raw internal tool/model events are not automatically exposed to clients.

## 18. Current AgentCore CLI

Current Strands Python deployment documentation recommends the newer AgentCore CLI for quick local/project workflows.

**Code sample — verified**

~~~bash
npm install -g @aws/agentcore
~~~

Current documented commands include:

**Code sample — verified**

~~~bash
agentcore create
agentcore dev
agentcore deploy
agentcore invoke
~~~

The current guide states that this CLI replaces the earlier bedrock-agentcore-starter-toolkit.

Do not start new automation around the deprecated toolkit.

For controlled enterprise promotion, Terraform and explicit CI/CD often provide better reviewability than an interactive local deployment command.

## 19. AgentCore custom-container contract

The current custom implementation guide requires:

- POST /invocations;
- GET /ping.

Its example uses FastAPI and a container built to AgentCore Runtime requirements.

Container architecture, runtime protocols, networking, and platform requirements can change independently of Strands, so validate them in the current AgentCore Runtime documentation for your pinned deployment.

## 20. Wrapper versus custom HTTP implementation

### AgentCore SDK wrapper

Use when:

- one simple entrypoint is enough;
- you want minimal server code;
- rapid deployment matters.

### Custom FastAPI/container

Use when:

- custom middleware;
- custom authentication flow;
- extra endpoints;
- advanced routing;
- custom protocol/server behavior

are required.

Do not add infrastructure complexity without a requirement.

## 21. Terraform support exists in the current AWS provider

The current official HashiCorp AWS provider exposes:

    aws_bedrockagentcore_agent_runtime

and:

    aws_bedrockagentcore_agent_runtime_endpoint

This lets runtime infrastructure participate in the same reviewed IaC workflow as the rest of the platform.

## 22. Minimal AgentCore Terraform shape

**Code sample — verified**

The resource structure below matches the current official HashiCorp AWS provider documentation.

~~~hcl
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "runtime" {
  name               = "bedrock-agentcore-runtime-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_bedrockagentcore_agent_runtime" "agent" {
  agent_runtime_name = "strands_mastery_agent"
  role_arn           = aws_iam_role.runtime.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.agent.repository_url}:release"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }
}
~~~

The official basic example also includes ECR read permissions on the runtime role.

Your real role additionally needs the exact model, session storage, and tool permissions required by your Agent.

The PUBLIC network mode shown by the provider example is not a blanket production recommendation. Select the current AgentCore network option that matches your threat model.

## 23. AgentCore endpoint resource

**Code sample — verified**

~~~hcl
resource "aws_bedrockagentcore_agent_runtime_endpoint" "agent" {
  name             = "production"
  agent_runtime_id = aws_bedrockagentcore_agent_runtime.agent.agent_runtime_id
  description      = "Production endpoint"
}
~~~

Use runtime versions/endpoints as part of your rollout and rollback design according to the current AWS/provider lifecycle model.

## 24. Runtime IAM needs more than ECR

The provider's minimal example demonstrates image-pull permission.

Your Agent may additionally need:

- Bedrock model invoke;
- S3 session/context storage;
- CloudWatch read APIs;
- Secrets Manager;
- telemetry;
- internal service access.

Build permissions from actual capabilities.

A review table is useful:

| Capability | Permission class | Resource scope | Reason |
| --- | --- | --- | --- |
| model | Bedrock invoke | required model/profile | reasoning |
| session | S3 read/write | session prefix | persistence |
| CloudWatch tool | read-only CloudWatch/Logs APIs | required account/log groups | diagnostics |
| external key | GetSecretValue | one secret | MCP/provider auth |

Exact ARN/resource conditions depend on your AWS services and region, so verify them in current IAM documentation.

## 25. Separate control-plane and runtime roles

CI/CD role:

    can provision/update approved infrastructure

Runtime role:

    can perform the Agent's runtime work

Keep them distinct.

A compromised runtime should not normally be able to:

- change its own IAM;
- replace its image;
- rewrite networking;
- delete its infrastructure.

## 26. Build immutable artifacts

The provider examples often use simple image tags for readability.

Production promotion should prefer an immutable release reference/process.

A strong flow:

    git SHA
      ↓
    build once
      ↓
    scan
      ↓
    publish immutable release tag/digest
      ↓
    dev
      ↓
    stage
      ↓
    prod uses the same artifact

Do not rebuild source separately for production after testing a different binary/image.

## 27. Container and dependency scanning

Before promotion:

- dependency vulnerability scan;
- OS package scan;
- secret scan;
- container scan;
- SBOM generation;
- license/provenance policy;
- MCP/plugin/Skill dependency review.

An Agent has normal supply-chain risk plus powerful runtime tool capability.

## 28. Health, synthetic testing, and evaluation are different

/ping answers:

    Is the process/runtime healthy enough to serve?

A synthetic invocation answers:

    Can the deployed stack complete a known safe request?

An eval suite answers:

    Does this Agent version behave correctly across a representative dataset?

Do not make the load balancer health check call a paid model.

## 29. Session persistence must match the compute target

Lambda:

    external persistence is required across invocations

Fargate/EKS:

    container filesystem is not a reliable multi-replica session store

AgentCore:

    runtime provides session-isolated execution capabilities,
    but application-level session/memory persistence still needs
    a deliberate design that matches your requirements.

Never assume local files survive replacement/scaling unless the platform explicitly guarantees it.

## 30. Autoscaling amplifies downstream load

Scaling from 2 replicas/sessions to 200 can multiply:

- model calls;
- MCP connections;
- CloudWatch queries;
- database traffic;
- external API requests.

Protect dependencies with:

- quotas;
- concurrency control;
- rate limits;
- bounded retries;
- connection pools;
- queue/backpressure.

Compute autoscaling does not remove provider/service limits.

## 31. Align timeouts end to end

Design:

    gateway deadline
      >
    Agent request deadline
      >
    child Agent/A2A deadline
      >
    tool deadline
      >
    downstream HTTP/SDK timeout

If the outer layer stops waiting while inner work continues, the system can spend tokens or perform side effects after the client has gone.

Propagate cancellation where supported.

## 32. Observability is part of deployment

Every environment should emit:

- traces;
- model/tool metrics;
- structured logs;
- runtime health;
- security/audit events.

Tag with bounded dimensions such as:

    environment
    release SHA
    model ID
    Agent version

so a rollout can be correlated with changes.

## 33. CI/CD pipeline

A serious pipeline looks like:

    pull request
      ↓
    format / lint / type checks
      ↓
    unit tests
      ↓
    dependency / secret / IaC scans
      ↓
    build immutable image
      ↓
    image scan + SBOM
      ↓
    deploy test environment
      ↓
    integration tests
      ↓
    Strands evaluation suite
      ↓
    Terraform plan review
      ↓
    deploy stage
      ↓
    synthetic invocation
      ↓
    promotion approval/policy
      ↓
    production canary/version
      ↓
    metrics + quality watch
      ↓
    broad promotion

Infrastructure success does not prove Agent behavioral quality.

## 34. Terraform plan is security evidence

Review changes to:

- IAM;
- runtime role;
- network mode;
- security groups/routes;
- secrets;
- environment variables;
- container URI;
- storage;
- endpoint/auth configuration.

A prompt/tool change alters behavior.

An IAM/network diff alters blast radius.

Both deserve review.

## 35. Rollback covers more than code

A release can include:

- image;
- model ID;
- system prompt;
- tools;
- Skill versions;
- steering rules;
- guardrail version;
- session schema;
- Terraform resources.

A rollback plan should restore a known compatible set.

Do not roll back only the container while leaving incompatible state or policy changes active.

## 36. Session/schema compatibility during rolling deploys

During a rollout:

    v1 and v2 may both read sessions

During rollback:

    v1 may read state written by v2

Test compatibility or use explicit migrations/versioning.

This is normal distributed-state engineering, not an AI-specific exception.

## 37. Target decision table

| Requirement | Lambda | Fargate | EKS | AgentCore Runtime |
| --- | --- | --- | --- | --- |
| Short event-style request | strong fit | fit | fit | fit |
| Streaming | current Strands tutorial: not implemented | strong | strong | strong |
| Long-running Agent | constrained by Lambda execution model | strong | strong | purpose-built |
| Minimal infrastructure operations | strong | medium | lower | strong |
| Kubernetes platform control | no | no | strongest | no |
| Container control | partial | strong | strongest | custom-container path |
| Agent-focused session isolation | app-managed | app-managed | app-managed | dedicated session microVM model |
| MCP/A2A protocol hosting | app-managed | app-managed | app-managed | purpose-built support |
| Existing Kubernetes platform | weak | medium | strongest | separate platform |
| Managed Agent-specific runtime | no | no | no | yes |

This is a decision aid, not a universal ranking.

## 38. Why the capstone uses AgentCore

The capstone uses AgentCore Runtime because it matches the teaching goals:

- managed Agent runtime;
- session isolation;
- Strands integration;
- long-running/streaming capabilities;
- MCP/A2A ecosystem;
- Terraform resource support.

The core application remains portable enough to move to Fargate or EKS if platform requirements change.

## 39. Production checklist

- [ ] Core Agent construction is separated from host adapter.
- [ ] Agent/session ownership is clear.
- [ ] Image is immutable/scanned and contains no credentials.
- [ ] Deployment and runtime IAM roles are separate.
- [ ] Runtime IAM follows actual tool capabilities.
- [ ] Ingress and egress are explicitly designed.
- [ ] Session storage is durable for the target.
- [ ] Timeout/cancellation layers align.
- [ ] Traces/logs/metrics/alarms deploy with the app.
- [ ] Infrastructure is managed as code.
- [ ] CI runs software, security, integration, and Agent eval gates.
- [ ] Promotion reuses the tested artifact.
- [ ] Rollback includes model/prompt/tool/policy compatibility.
- [ ] Post-deploy synthetic verification exists.

## Sources checked

- https://strandsagents.com/docs/user-guide/sdk/deploy/
- https://strandsagents.com/docs/user-guide/sdk/deploy/deploy_to_aws_lambda/
- https://strandsagents.com/docs/user-guide/sdk/deploy/deploy_to_aws_fargate/
- https://strandsagents.com/docs/user-guide/sdk/deploy/deploy_to_amazon_eks/
- https://strandsagents.com/docs/user-guide/deploy/deploy_to_bedrock_agentcore/python/
- https://strandsagents.com/docs/user-guide/sdk/deploy/operating-agents-in-production/
- https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/bedrockagentcore_agent_runtime.html.markdown
- https://github.com/hashicorp/terraform-provider-aws/blob/main/website/docs/r/bedrockagentcore_agent_runtime_endpoint.html.markdown
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 20 — Capstone: Build & Ship a Production Multi-Agent System](20-capstone-build-ship-production-multi-agent-system.md). We will build one complete incident-triage system with specialist Agents, real AWS MCP tools, persistent sessions, hook policy, guardrails, OpenTelemetry, evaluation, AgentCore Runtime, Terraform, CI/CD, and rollback.

Back to the [course README](../README.md).
