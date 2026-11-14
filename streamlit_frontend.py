
import streamlit as st
import uuid

from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

# Generate unique thread ID
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = str(uuid.uuid4())

CONFIG = {
    'configurable': {
        'thread_id': st.session_state['thread_id']
    }
}

# Initialize message history
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Display previous conversation
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# User input
user_input = st.chat_input('Type here')

if user_input:

    # Display user message
    st.session_state['message_history'].append(
        {'role': 'user', 'content': user_input}
    )

    with st.chat_message('user'):
        st.text(user_input)

    # Invoke LangGraph chatbot
    response = chatbot.invoke(
        {'messages': [HumanMessage(content=user_input)]},
        config=CONFIG
    )

    # Extract AI response
    ai_message = response['messages'][-1].content

    # Store AI response
    st.session_state['message_history'].append(
        {'role': 'assistant', 'content': ai_message}
    )

    with st.chat_message('assistant'):
        st.text(ai_message)
