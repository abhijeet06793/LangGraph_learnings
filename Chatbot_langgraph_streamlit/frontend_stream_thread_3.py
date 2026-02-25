from concurrent.futures import thread
import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# Set page configuration
st.set_page_config(page_title="LangGraph Chatbot", page_icon="🤖", layout="wide")

# Initialize session state for chat history and thread_id
if "messages" not in st.session_state: #st.session_state is a dictionary by itself, it can store any key-value pairs and persist them across interactions. Here we are using it to store the chat history and thread_id for each user session.
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    # Generate a unique thread_id for this session
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = []
    st.session_state.chat_threads.append(st.session_state.thread_id)

# Page title
st.title("🤖 LangGraph Chatbot")
st.caption("Powered by LLM, LangGraph and Streamlit")

# Display chat history
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)

# Chat input (this doesn't cause page refresh!)
user_input = st.chat_input("Type your message here...")

if user_input:
    # Create HumanMessage from user input
    human_message = HumanMessage(content=user_input)
    
    # Add user message to session state
    st.session_state.messages.append(human_message)
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get AI response with streaming
    with st.chat_message("assistant"):
        # Configure thread for persistence
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        
        # Stream the response and display with typing effect
        chatbot_generator = chatbot.stream(
            {"messages": [human_message]}, 
            config=config, 
            stream_mode="messages"
        )
        
        # st.write_stream handles the streaming display and returns the complete text as string object
        ai_response_text = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot_generator 
            if message_chunk.content  # Filter out empty chunks
        )
        # Create AIMessage object from the complete response
        ai_message = AIMessage(content=ai_response_text)
        
        # Add AI message to session state
        st.session_state.messages.append(ai_message)

    
# # Sidebar with options
with st.sidebar:
    st.title("✨ Chatbot Options")
    st.markdown(
        """
        <style>
        .sidebar-title { font-size: 1.3em; font-weight: bold; color: #4F8BF9; }
        .sidebar-info { font-size: 1em; color: #333; margin-bottom: 10px; }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="sidebar-info" style="color:#FF5733;">Manage your conversations and view session details below.</div>', unsafe_allow_html=True) 

if st.sidebar.button("New Chat", icon_position="left"):

    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.chat_threads.append(st.session_state.thread_id)
    st.session_state.messages = []
    st.rerun()



st.sidebar.header("My Conversations", text_alignment="left", divider=True)

# Show most recent thread (latest conversation)
latest_thread = st.session_state.chat_threads[-1]
st.sidebar.markdown("<p style='color:#4F8BF9; font-weight:bold;'>Latest Conversation:</p>", unsafe_allow_html=True)
if st.sidebar.button(f"{latest_thread[:8]}... (Latest)", key=f"latest_{latest_thread}"):
    st.session_state.thread_id = latest_thread
    # Load messages for this thread from the chatbot's state history
    state_history = chatbot.get_state(config={"configurable": {"thread_id": st.session_state.thread_id}})
    if state_history.values:
        st.session_state.messages = state_history.values["messages"]
    else:
        st.session_state.messages = []
    st.rerun()

# Show older conversations
if len(st.session_state.chat_threads) > 1:
    st.sidebar.markdown("<p style='color:#FF7F50; font-weight:bold;'>Older Conversations:</p>", unsafe_allow_html=True)
    for older_thread in reversed(st.session_state.chat_threads[:-1]):
        if st.sidebar.button(f"{older_thread[:8]}...", key=f"older_{older_thread}"):
            st.session_state.thread_id = older_thread
            # Load messages for this thread from the chatbot's state history
            state_history = chatbot.get_state(config={"configurable": {"thread_id": st.session_state.thread_id}})
            if state_history.values:
                st.session_state.messages = state_history.values["messages"]
            else:
                st.session_state.messages = []
            st.rerun()




# # Sidebar with options
# with st.sidebar:
#     st.header("Chat Options")
    
#     if st.button("🗑️ Clear Chat History"):
#         st.session_state.messages = []
#         st.session_state.thread_id = str(uuid.uuid4())
#         st.rerun()
    
#     st.divider()
    
#     st.subheader("Session Info")
#     st.write(f"**Thread ID:** `{st.session_state.thread_id[:8]}...`")
#     st.write(f"**Messages:** {len(st.session_state.messages)}")

