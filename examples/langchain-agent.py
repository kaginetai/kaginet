"""
LangChain agent with Kaginet payment tools.

Creates a LangChain agent that can create escrows, check status,
and release payments using Kaginet's 29 tools.

Prerequisites:
    pip install kagikai-langchain langchain-openai
    export KAGINET_API_KEY=kagi_your_api_key_here
    export OPENAI_API_KEY=sk-...
"""

import os

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from kagikai_langchain import KagikaiToolkit

# Initialize the toolkit
toolkit = KagikaiToolkit(
    base_url="https://mcp.kaginet.com",
    api_key=os.environ["KAGINET_API_KEY"],
)
tools = toolkit.get_tools()

# Create the agent
llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a payment agent. You can create Bitcoin escrows, "
        "check instrument status, verify attestations, and release payments. "
        "Always confirm the funding address and amount with the user before proceeding."
    )),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def main():
    result = executor.invoke({
        "input": (
            "Create a 25,000 sat escrow to bc1qexampleaddress "
            "for 'API integration testing'. Use hash_match evaluator."
        ),
    })
    print(f"\nAgent response: {result['output']}")


if __name__ == "__main__":
    main()
