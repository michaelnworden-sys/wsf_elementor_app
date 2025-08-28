import streamlit as st
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
import uuid
import json

# --- CRITICAL: PASTE YOUR INFO HERE ---

# 1. PASTE YOUR PROJECT ID
PROJECT_ID = "lumina-content-intelligence"

# 2. PASTE YOUR AGENT ID
AGENT_ID = "39100170-63ca-4c8e-8c10-b8d6c1d1b55a"

# --- DO NOT EDIT BELOW THIS LINE ---

# This function connects to and talks with your Dialogflow agent
def detect_intent_texts(text, session_id):
    location = "global"
    client_options = {"api_endpoint": f"{location}-dialogflow.googleapis.com"}
    
    try:
        # Try to get credentials from Streamlit secrets
        credentials_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        # Create the session client - using the working approach
        session_client = dialogflow.SessionsClient(client_options=client_options, credentials=credentials)
        
        session_path = session_client.session_path(
            project=PROJECT_ID, location=location, agent=AGENT_ID, session=session_id
        )
        
        text_input = dialogflow.TextInput(text=text)
        query_input = dialogflow.QueryInput(text=text_input, language_code="en")
        request = dialogflow.DetectIntentRequest(
            session=session_path, query_input=query_input
        )
        response = session_client.detect_intent(request=request)
        
        response_messages = [
            " ".join(msg.text.text) for msg in response.query_result.response_messages
        ]
        return " ".join(response_messages)
        
    except Exception as e:
        st.error(f"An error occurred with Dialogflow: {e}")
        return None

# --- Streamlit User Interface ---

st.title("San Juan Playbooks")

# Initialize chat history and session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get new user input
if user_input := st.chat_input("Ask your question:"):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get the agent's response
    with st.spinner("Thinking..."):
        agent_response = detect_intent_texts(user_input, st.session_state.session_id)

    # Add agent response to history and display it
    if agent_response:
        st.session_state.messages.append({"role": "assistant", "content": agent_response})
        with st.chat_message("assistant"):
            st.markdown(agent_response)