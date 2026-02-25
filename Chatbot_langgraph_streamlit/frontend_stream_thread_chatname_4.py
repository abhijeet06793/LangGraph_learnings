import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid
from backend import llm_model
from dotenv import load_dotenv
import os
from euriai.langchain import create_chat_model

load_dotenv()
api_key = os.getenv("key")

# Set page configuration
st.set_page_config(page_title="LangGraph Chatbot", page_icon="🤖", layout="wide")

# Initialize session state for chat history and thread_id
if "messages" not in st.session_state: #st.session_state is a dictionary by itself, it can store any key-value pairs and persist them across interactions. Here we are using it to store the chat history and thread_id for each user session.
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    # Generate a unique thread_id for this session
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_name_kv" not in st.session_state:
    st.session_state.chat_name_kv = {}
    st.session_state.chat_name_kv[st.session_state.thread_id] = "No chat available"  # Default name for first chat

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
        
        # Stream the response and display with typing effect. This is a generator object. chatbot is a workflow.
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
        
        # Handle empty response
        if not ai_response_text or ai_response_text.strip() == "":
            ai_response_text = "I apologize, but I couldn't generate a response. Please try again."
        
        # Create AIMessage object from the complete response
        ai_message = AIMessage(content=ai_response_text)
        
        # Add AI message to session state
        st.session_state.messages.append(ai_message)

# Sidebar with options
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

    st.divider()
    
    # New Chat button with better styling
    if st.button("🆕 Start new chat", type="primary", use_container_width=True):

        older_state = chatbot.get_state(config={"configurable": {"thread_id": st.session_state.thread_id}})
        if older_state.values and older_state.values.get("messages"):
            older_state_messages = older_state.values["messages"]
            
            # Extract text content from messages for LLM
            conversation_text = "\n".join([
                f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}" 
                for msg in older_state_messages[-10:]  # Only use last 10 messages to avoid token limits
            ])
            
            # Generate chat summary from messages with error handling
            try:
                chat_name = llm_model(api_key=api_key).invoke(
                    f"Create a concise and meaningful topic name (max 5 words) that accurately represents the following chat conversation:\n\n{conversation_text}"
                )
                # Truncate if too long
                chat_name_text = chat_name.content.strip()
                if len(chat_name_text) > 50:  # Limit to 50 characters
                    chat_name_text = chat_name_text[:47] + "..."
                st.session_state.chat_name_kv[st.session_state.thread_id] = chat_name_text
            except Exception as e:
                # Fallback to generic name if LLM fails
                st.session_state.chat_name_kv[st.session_state.thread_id] = f"Chat {len(st.session_state.chat_threads)}"
                st.error(f"Failed to generate chat name: {str(e)}")
        else:
            st.session_state.chat_name_kv[st.session_state.thread_id] = "Empty Chat"

        # Create new thread
        new_thread_id = str(uuid.uuid4())
        st.session_state.thread_id = new_thread_id
        st.session_state.chat_threads.append(new_thread_id)
        st.session_state.messages = []
        st.session_state.chat_name_kv[new_thread_id] = "No chat available"  # Default name for new chat
        st.rerun()


    st.header("My Conversations", divider=True)

    # Show current active thread (latest conversation)
    if st.session_state.thread_id:
        current_thread = st.session_state.thread_id
        # Get chat name from chat_name_kv
        current_chat_name = st.session_state.chat_name_kv.get(current_thread, "No chat available")
        st.markdown("<p style='color:#4F8BF9; font-weight:bold;'>Current Conversation:</p>", unsafe_allow_html=True)
        st.markdown(f"**📝 {current_chat_name}**")
        st.divider()

    # Show other conversations (all except current active one)
    other_threads = [t for t in st.session_state.chat_threads if t != st.session_state.thread_id]
    if len(other_threads) > 0:
        st.markdown("<p style='color:#FF7F50; font-weight:bold;'>Other Conversations:</p>", unsafe_allow_html=True)
        # Show in reverse order (newest first)
        for other_thread in reversed(other_threads):
            # Get chat name from chat_name_kv, fallback to thread_id if not found
            chat_display_name = st.session_state.chat_name_kv.get(other_thread, f"{other_thread[:8]}...")
            if st.button(f"📄 {chat_display_name}", key=f"thread_{other_thread}", use_container_width=True):
                st.session_state.thread_id = other_thread
                # Load messages for this thread from the chatbot's state history
                try:
                    state_history = chatbot.get_state(config={"configurable": {"thread_id": st.session_state.thread_id}})
                    if state_history.values and state_history.values.get("messages"):
                        st.session_state.messages = state_history.values["messages"]
                    else:
                        st.session_state.messages = []
                except Exception as e:
                    st.error(f"Failed to load conversation: {str(e)}")
                    st.session_state.messages = []
                st.rerun()
