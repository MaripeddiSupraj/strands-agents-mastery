from strands import Agent
from strands.memory import MemoryManager
from strands.vended_memory_stores.test_memory_store import TestMemoryStore


store = TestMemoryStore(name="incident-notes")

memory = MemoryManager(
    stores=[store],
    add_tool_config=True,
)

agent = Agent(memory_manager=memory)

print(
    agent(
        "Remember that the payments-api owner is the Payments Platform team, "
        "then tell me what you stored."
    )
)

print(agent("Who owns payments-api? Use memory if relevant."))
