resource "aws_bedrockagentcore_agent_runtime" "incident_triage" {
  agent_runtime_name = "incident_triage"
  role_arn           = aws_iam_role.agent_runtime.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${var.container_uri}"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }
}

resource "aws_bedrockagentcore_agent_runtime_endpoint" "incident_triage" {
  name             = "incident-triage-endpoint"
  agent_runtime_id = aws_bedrockagentcore_agent_runtime.incident_triage.agent_runtime_id
  description      = "Incident triage AgentCore endpoint"
}

variable "container_uri" {
  type        = string
  description = "Immutable tested container URI or digest."
}

# Define aws_iam_role.agent_runtime separately with only the exact runtime
# permissions required by your model, read-only telemetry tools, memory and
# approved telemetry export path. See Lesson 20 for the IAM design.
