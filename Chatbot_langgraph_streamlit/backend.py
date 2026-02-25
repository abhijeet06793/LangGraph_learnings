from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List
import operator
from dotenv import load_dotenv
import os
from euriai.langchain import create_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph.message import add_messages
import time

load_dotenv()
api_key = os.getenv("key")

def llm_model(api_key):
    chat_model = create_chat_model(
        api_key=api_key,
        model="gpt-4.1-nano",
        temperature=0.7)
    return chat_model

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state["messages"]
    # Get the AI response
    response = llm_model(api_key).invoke(messages)
    # Return AIMessage object, not just the string content
    return {"messages": [response]}

checkpoint_saver = InMemorySaver()

graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)

graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpoint_saver)

# config1 = {"configurable": {"thread_id": "1"}}
# final_state = chatbot.invoke({"messages": [HumanMessage(content="Hi how are you?")]}, config=config1)
# final_state