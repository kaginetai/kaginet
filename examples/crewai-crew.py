"""
CrewAI crew with Kaginet escrow capability.

Creates a two-agent crew: a project manager that negotiates terms
and a payment agent that handles the Bitcoin escrow.

Prerequisites:
    pip install kagikai-crewai crewai
    export KAGINET_API_KEY=kagi_your_api_key_here
    export OPENAI_API_KEY=sk-...
"""


from crewai import Agent, Crew, Task

from kagikai_crewai import (
    KagikaiEscrowCreateTool,
    KagikaiEscrowStatusTool,
    KagikaiEscrowReleaseTool,
    KagikaiFeeEstimateTool,
    KagikaiHealthTool,
)

# Initialize payment tools
escrow_tools = [
    KagikaiHealthTool(),
    KagikaiEscrowCreateTool(),
    KagikaiEscrowStatusTool(),
    KagikaiEscrowReleaseTool(),
    KagikaiFeeEstimateTool(),
]

# Agent: Payment handler
payment_agent = Agent(
    role="Payment Agent",
    goal="Handle Bitcoin escrow payments for completed work",
    backstory=(
        "You manage Bitcoin escrow payments. You create escrows when work "
        "is agreed upon, monitor funding status, and release payments when "
        "evidence of completion is provided."
    ),
    tools=escrow_tools,
    verbose=True,
)

# Agent: Project manager
pm_agent = Agent(
    role="Project Manager",
    goal="Coordinate work delivery and approve payments",
    backstory=(
        "You manage projects. When work is completed satisfactorily, "
        "you instruct the payment agent to release the escrow."
    ),
    verbose=True,
)

# Tasks
create_escrow_task = Task(
    description=(
        "First check the service health, then estimate fees for a 50,000 sat escrow. "
        "If healthy and fees are acceptable, create a 50,000 sat escrow to "
        "bc1qexampleaddress for 'Website redesign project'. "
        "Use hash_match evaluator."
    ),
    expected_output="Escrow instrument ID and funding address",
    agent=payment_agent,
)

check_status_task = Task(
    description=(
        "Check the status of the escrow created in the previous task. "
        "Report whether it has been funded."
    ),
    expected_output="Current escrow status",
    agent=payment_agent,
)

# Crew
crew = Crew(
    agents=[payment_agent, pm_agent],
    tasks=[create_escrow_task, check_status_task],
    verbose=True,
)


def main():
    result = crew.kickoff()
    print(f"\nCrew result: {result}")


if __name__ == "__main__":
    main()
