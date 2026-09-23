# EXPERIMENTAL: current Strands BidiAgent API.
# Requires a supported realtime model and current audio dependencies.

import asyncio

from strands.experimental.bidi import BidiAgent, BidiAudioIO
from strands.experimental.bidi.models import BedrockNovaSonicModel


model = BedrockNovaSonicModel()
agent = BidiAgent(
    model=model,
    system_prompt=(
        "You are a concise incident-response voice assistant. "
        "Separate evidence from hypotheses."
    ),
)
audio_io = BidiAudioIO()


async def main():
    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output()],
    )


asyncio.run(main())
