from bedrock_agentcore.runtime import BedrockAgentCoreApp

from local import commander


app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    prompt = payload["prompt"]

    result = commander(
        prompt,
        limits={"turns": 8, "output_tokens": 3000, "total_tokens": 30000},
    )

    return {
        "message": result.message,
        "stop_reason": result.stop_reason,
    }


if __name__ == "__main__":
    app.run()
