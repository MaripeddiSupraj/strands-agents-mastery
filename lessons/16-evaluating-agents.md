# Lesson 16 — Evaluating Agents

Strands Agents Mastery → Phase 5 — Production Readiness

A demo tells you that an Agent worked once.

An evaluation tells you whether a specific Agent version works across a defined set of cases, how often it fails, and what changed after a model, prompt, tool, or orchestration update.

For production agents, evaluation is not optional QA added at the end. It is the closest thing you have to a regression test for probabilistic behavior.

## Map of this lesson

- Software tests versus Agent evaluations
- The current Strands Evals SDK
- Cases, tasks, experiments, and evaluators
- Output evaluation
- Tool-selection and parameter evaluation
- Goal success and failure behavior
- Deterministic evaluators
- Multi-agent trajectory evaluation
- Safety and red-team cases
- Cost and latency gates
- Judge-model risk
- Building a representative dataset
- CI/CD integration
- Online versus offline evaluation


## Recommended hands-on example — Turn the incident assistant into a regression suite

> **Build today:** Create a small evaluation dataset around the same payments-api assistant instead of judging it from one good demo.
>
> Include at least five cases: correct telemetry routing, telemetry unavailable, AWS documentation lookup, prompt injection inside a log line, and a dangerous “restart production” request.
>
> **Measure:** correct specialist/tool selection, correct parameters, evidence-vs-hypothesis discipline, goal success, policy compliance, latency, and token cost.
>
> **Change one thing:** swap the model or alter the system prompt, rerun the exact same dataset, and compare.
>
> **Why this example:** it shows the learner what evaluation is for—proving that a change preserved or improved behavior rather than saying “it looked good when I tried it.”

Keep deterministic authorization tests outside the LLM eval suite. Evals complement software tests; they do not replace them.


## 1. Why normal unit tests are not enough

A normal function can often be tested like:

    input X
      → exact output Y

An Agent may produce two different but equally correct explanations.

Exact-string assertions are therefore often the wrong test.

At the same time, an Agent still contains deterministic software that absolutely should use normal tests.

Use two layers.

### Deterministic tests

Test:

- argument validation;
- authorization;
- routing predicates;
- parser/schema logic;
- hook policy;
- idempotency;
- timeout mapping;
- session isolation.

### Behavioral evaluation

Measure:

- answer quality;
- correct tool choice;
- correct tool parameters;
- task completion;
- instruction following;
- failure communication;
- recovery behavior;
- multi-agent trajectory.

Do not replace unit tests with LLM judges.

## 2. Install the current Strands Evals SDK

Current official documentation installs the evaluation package separately from the core Agent SDK.

**Code sample — verified**

~~~bash
pip install strands-agents-evals strands-agents
~~~

The evaluation package evolves independently enough that you should pin it in your project lockfile.

Current evaluators can use the same model-provider ecosystem as Strands. The current quickstart uses Amazon Bedrock as the default judge-model path.

## 3. The four basic pieces

A useful evaluation model is:

    Case
      = one input + expected information/metadata

    Task
      = the Agent/application being exercised

    Evaluator
      = how behavior is scored

    Experiment
      = cases × evaluators × task
        → report

This separation is important.

Do not hide the test dataset inside the Agent prompt.

## 4. Your first experiment

**Code sample — verified**

The API shape below follows the current Strands evaluation quickstart.

~~~python
from strands import Agent
from strands_evals import eval_task, Case, Experiment
from strands_evals.evaluators import OutputEvaluator

@eval_task()
def get_response():
    return Agent(
        system_prompt=(
            "You are a helpful assistant that provides accurate information."
        ),
        callback_handler=None,
    )

test_cases = [
    Case[str, str](
        name="knowledge-1",
        input="What is the capital of France?",
        expected_output="The capital of France is Paris.",
        metadata={"category": "knowledge"},
    ),
    Case[str, str](
        name="math-1",
        input="What is 2 + 2?",
        expected_output="4",
        metadata={"category": "math"},
    ),
]

evaluator = OutputEvaluator(
    rubric="""
    Evaluate the response based on:
    1. Accuracy
    2. Completeness
    3. Clarity

    Score 1.0 if all criteria are met excellently.
    Score 0.5 if some criteria are partially met.
    Score 0.0 if the response is inadequate or incorrect.
    """,
    include_inputs=True,
)

experiment = Experiment[str, str](
    cases=test_cases,
    evaluators=[evaluator],
)

report = experiment.run_evaluations(get_response)
report.run_display()

experiment.to_file("basic_evaluation")
~~~

This is only the starting point.

A production dataset should model your real task distribution and failure modes.

## 5. OutputEvaluator is an LLM judge

Current OutputEvaluator scores model output against a rubric.

It is useful for subjective properties such as:

- correctness where reference comparison is semantic;
- relevance;
- completeness;
- clarity;
- adherence to domain expectations.

But remember:

    Agent model can be wrong
    and
    judge model can also be wrong

LLM-as-a-judge is measurement, not ground truth.

Use deterministic checks where possible.

## 6. A good rubric is specific

Weak:

    “Is this a good answer?”

Better:

    “Score 1.0 only if the answer:
     - reports the service status from tool evidence;
     - does not invent a root cause;
     - identifies missing evidence explicitly;
     - gives no write/remediation claim unless a write tool succeeded.”

A precise rubric improves reproducibility and debugging.

Keep the rubric under version control.

## 7. Tool selection needs its own evaluation

An Agent can give a plausible final answer after taking a wasteful or unsafe path.

Current Strands Evals includes ToolSelectionAccuracyEvaluator.

It operates at tool-call level and evaluates whether the chosen tool was justified in the conversation context.

This helps find:

- unnecessary tool calls;
- wrong tool choice;
- premature action;
- skipped required tool.

That is often more useful than evaluating final prose alone.

## 8. Tool parameter accuracy matters separately

Selecting the correct tool is only half the job.

Example:

    correct tool: get_logs
    wrong arguments:
      service = payments-prod
      environment = dev

A production evaluation should separately check tool parameter accuracy.

Current evaluator families include ToolParameterAccuracyEvaluator for this purpose.

When a parameter can be checked deterministically, also validate it in application code.

Evaluation detects behavior; validation blocks unsafe behavior.

## 9. Goal success is an end-to-end metric

Current Strands Evals includes GoalSuccessRateEvaluator at session level.

This is useful for questions such as:

    Did the user actually get the requested outcome?

rather than:

    Did the final paragraph look polished?

For an incident Agent, goal success could mean:

- gathered required evidence;
- correctly identified uncertainty;
- produced a bounded recommendation;
- did not perform unapproved writes.

Define success in business terms.

## 10. Evaluate failure behavior

Production Agents fail.

Current Agentic evaluator family includes evaluators such as:

- FailureCommunicationEvaluator;
- PartialCompletionEvaluator;
- RecoveryStrategyEvaluator.

Use them.

A good Agent should be able to say:

    “CloudWatch lookup failed with AccessDenied.
     I verified deployment status from source B,
     but I cannot confirm error-rate evidence.”

A bad Agent says:

    “Everything looks healthy.”

after a required tool failed.

## 11. Deterministic evaluators are valuable in CI

Current Strands Evals includes fast code-based deterministic evaluators such as checks for equality, containment, tool called, state equality, and skill invocation.

Use deterministic evaluators whenever the requirement is crisp.

Examples:

- refund tool must never be called in read-only mode;
- approval skill must be invoked before publish;
- final JSON must contain required key;
- a specific safe tool must be used for a regulated lookup.

These tests are cheaper and less noisy than an LLM judge.

## 12. Evaluate the trajectory, not just output

For multi-agent and tool-heavy systems, the path matters.

Example expected trajectory:

    intake
      → read incident
      → read metrics
      → documentation specialist
      → synthesize

Unsafe trajectory:

    intake
      → restart production
      → read metrics
      → claim fixed

Both could end with similar prose.

Trajectory evaluation catches this difference.

Current evaluator catalog includes tool-level and session/trace-level Agentic evaluators. Choose the granularity that matches the requirement.

## 13. Multi-agent routing should be measured

For Agents-as-Tools:

- correct specialist chosen;
- unnecessary specialists avoided;
- child request contains the right context.

For Graph:

- expected branches executed;
- forbidden branches not executed;
- cycles converge or hit a bound.

For Swarm:

- handoffs are useful;
- repetitive handoffs are low;
- correct specialist terminates the task.

A multi-agent evaluation report should include both quality and orchestration cost.

## 14. Skills need Skill-specific evaluation

Current Strands Evals includes Skill evaluator families for:

- SkillSelectionAccuracyEvaluator;
- SkillInstructionFollowingEvaluator.

This is useful because a Skills system has two failure stages:

1. Agent chooses the wrong Skill.
2. Agent chooses the correct Skill but fails to follow its instructions.

Measure both separately.

## 15. Build a dataset from real failure classes

A strong dataset is not 100 variations of the happy path.

Include:

### Normal cases

Representative daily requests.

### Edge cases

Missing IDs, ambiguous service names, incomplete user context.

### Tool failures

Timeout, AccessDenied, 5xx, malformed result.

### Budget failures

Turn limit, token limit, cancellation.

### Security cases

Prompt injection in tool output, untrusted user claims, cross-tenant request.

### Policy cases

PII, blocked topic, guardrail intervention.

### Multi-agent cases

Wrong specialist temptation, handoff loop, unavailable remote A2A Agent.

### Long-context cases

Critical old fact buried under noisy history.

This dataset becomes one of your most valuable production assets.

## 16. Do not train your prompt only to the eval set

If you repeatedly modify the prompt until 30 fixed examples pass, you can overfit.

Maintain:

- development set;
- holdout regression set;
- production-derived cases;
- periodic newly sampled cases.

Do not expose sensitive production transcripts directly to a broad development dataset. De-identify and follow your data policy.

## 17. Judge-model selection is a measurement decision

If an evaluator uses an LLM judge, record:

- provider;
- model ID;
- judge prompt/rubric version;
- date/version;
- temperature/config where relevant.

If the judge model changes, scores may move even when the Agent did not.

Treat the evaluator configuration as part of the benchmark version.

## 18. IAM for evaluation

If the default evaluator judge uses Bedrock, the CI or evaluation workload needs Bedrock model invocation permission.

Do not give the CI role broad production AWS permissions merely because the Agent under test normally has them.

A safer evaluation account/environment uses:

- read-only or mocked external systems where possible;
- synthetic data;
- least-privilege Bedrock invoke permissions;
- dedicated secrets;
- no production destructive credentials.

Behavioral tests should not accidentally mutate production.

## 19. Evaluate cost and latency alongside quality

A model update that raises goal success from 94% to 95% but doubles cost and latency may or may not be acceptable.

Track per test case:

- total tokens;
- model call count;
- tool count;
- turns;
- duration;
- specialist/handoff count;
- expensive external API calls.

Set an allowed regression budget.

Quality gates without cost gates can produce an Agent that becomes economically unusable.

## 20. A practical release gate

An illustrative production policy:

    deterministic security tests = 100% pass

    tool-selection accuracy >= agreed threshold

    goal-success score >= baseline threshold

    unsafe action rate = 0 in protected test set

    p95 token use <= budget

    p95 latency <= SLO test budget

    no statistically meaningful regression
    against current production baseline

The exact thresholds are business decisions.

Do not copy arbitrary percentages from this course.

## 21. Baseline every important change

Run the same experiment before and after:

- model change;
- system prompt change;
- tool description change;
- new tool;
- context strategy change;
- Skill change;
- steering policy change;
- multi-agent topology change.

Compare:

    baseline
      versus
    candidate

Without a baseline, one good-looking report means little.

## 22. Run evaluations concurrently carefully

Current Experiment supports asynchronous evaluation.

Concurrency speeds a large suite, but it can:

- hit provider throttling;
- overload MCP/downstream test systems;
- distort latency measurements.

Separate:

    correctness-evaluation concurrency

from:

    realistic load/performance test

Do not interpret a throttled 100-way eval run as normal user latency.

## 23. Save experiment artifacts

Current quickstart supports serializing an Experiment.

Store with your CI artifact/release evidence:

- experiment configuration;
- case-set version/hash;
- Agent git SHA;
- model configuration;
- evaluator configuration;
- scores;
- failure examples;
- token/latency summary.

This gives you provenance for “why did we approve this Agent version?”

## 24. Use the CLI in CI, but pin its behavior

The current Strands evaluation package includes a command-line interface for running and managing evaluations.

Because CLI subcommands can evolve, build CI against your pinned package version and use the current CLI reference when authoring the workflow.

The CI principle is stable:

    build
      → unit tests
      → security/static checks
      → Agent eval suite
      → threshold validation
      → package/deploy candidate

Do not manually inspect one terminal report as the only gate.

## 25. Online evaluation complements offline evaluation

Offline evaluation:

- repeatable;
- controlled;
- safe;
- useful before release.

Online signals:

- real tool errors;
- user abandonment;
- latency;
- token usage;
- escalation rate;
- sampled quality review.

Production traffic exposes cases your static suite missed.

Feed de-identified, approved failure patterns back into the offline dataset.

## 26. Evaluation is not monitoring

Evaluation asks:

    Did the Agent do the right thing?

Monitoring asks:

    Is the system operating normally right now?

You need both.

Lesson 17 builds the observability layer that makes production behavior measurable.

## 27. Production checklist

- [ ] Unit tests and behavioral evaluations are separate.
- [ ] Dataset includes failures, security, and edge cases.
- [ ] Tool selection and parameters are evaluated.
- [ ] Goal success is measured.
- [ ] Failure communication/recovery is tested.
- [ ] Multi-agent trajectory is evaluated.
- [ ] Deterministic checks are preferred for deterministic requirements.
- [ ] Judge configuration is versioned.
- [ ] Cost and latency are part of release comparison.
- [ ] Candidate is compared with a baseline.
- [ ] Evaluation runs in a safe non-production environment.
- [ ] CI stores evaluation evidence with the release.

## Sources checked

- https://strandsagents.com/docs/user-guide/evals-sdk/quickstart/
- https://strandsagents.com/docs/user-guide/evals-sdk/evaluators/
- https://strandsagents.com/docs/user-guide/evals-sdk/evaluators/tool_selection_evaluator/
- https://strandsagents.com/docs/user-guide/evals-sdk/evaluators/output_evaluator/
- https://github.com/strands-agents/harness-sdk

## What’s next

Continue to [Lesson 17 — Observability: Traces, Metrics & Logs](17-observability-traces-metrics-logs.md). We will make each model turn, tool call, specialist, token, latency spike, and failure diagnosable in production.

Back to the [course README](../README.md).
