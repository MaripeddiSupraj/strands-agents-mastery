import sys
from pathlib import Path

from strands import Agent
from strands.session import SnapshotSessionManager
from strands.storage import LocalFileStorage


mode = sys.argv[1] if len(sys.argv) > 1 else "first"
session_dir = Path(__file__).parent / "sessions"

session_manager = SnapshotSessionManager(
    session_id="inc-2841",
    storage=LocalFileStorage(str(session_dir)),
)

agent = Agent(session_manager=session_manager)

if mode == "first":
    prompt = (
        "Remember this incident: INC-2841 payments-api began returning 5xx "
        "errors around 10:12 UTC and latency increased at the same time."
    )
elif mode == "resume":
    prompt = (
        "Continue INC-2841. What have we already established, and what "
        "evidence should we gather next?"
    )
else:
    raise SystemExit("Use: python main.py first | resume")

print(agent(prompt))
