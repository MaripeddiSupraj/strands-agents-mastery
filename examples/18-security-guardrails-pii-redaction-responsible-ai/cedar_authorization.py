from strands import Agent, tool
from strands.vended_interventions.cedar import CedarAuthorization


@tool
def search(query: str) -> str:
    """Search synthetic incident records."""
    return f"Results for: {query}"


@tool
def delete_record(record_id: str) -> str:
    """Illustrative destructive tool."""
    return f"SECURITY FAILURE: deleted {record_id}"


cedar = CedarAuthorization(
    policies=(
        'permit(principal, action == Action::"search",'
        " resource);"
    ),
)

agent = Agent(
    tools=[search, delete_record],
    interventions=[cedar],
)

print(
    agent(
        "Search for payments-api incident records, then delete record 42."
    )
)
