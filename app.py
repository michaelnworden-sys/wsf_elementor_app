import streamlit as st
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
import uuid
import json

# Add this CSS injection function
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Apply Poppins font to everything */
    .main, .stApp, html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* User avatar - WSF teal with white icon */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div[class*="st-emotion-cache"] {
        background-color: #00A693 !important;
        color: white !important;
        border-radius: 12px !important;
    }
    
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) svg {
        color: white !important;
        fill: white !important;
    }
    
    /* Assistant avatar - teal blue like the "Make reservations" button */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[class*="st-emotion-cache"] {
        background-color: #0891B2 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
    }
    
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) svg {
        color: white !important;
        fill: white !important;
    }
    
    /* COMPLETELY CLEAN WHITE CHAT MESSAGE BOXES */
    [data-testid="stChatMessage"] {
        background-color: white !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
    }
    
    /* Remove ALL borders and outlines from message content */
    [data-testid="stChatMessage"] > div,
    [data-testid="stChatMessage"] > div > div,
    [data-testid="stChatMessage"] * {
        background-color: white !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    [data-testid="stChatMessage"]:hover {
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* SIMPLE BLACK TEXT IN CHAT MESSAGES */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] div {
        color: black !important;
        background-color: white !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 16px !important;
        line-height: 1.5 !important;
        margin: 0 !important;
        border: none !important;
        outline: none !important;
    }
    
    /* Clean up chat input styling - keep this nice */
    [data-testid="stChatInput"] {
        background-color: white !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    [data-testid="stChatInput"] > div {
        background-color: white !important;
        border: 2px solid #00A693 !important;
        border-radius: 25px !important;
        box-shadow: 0 4px 12px rgba(0, 166, 147, 0.15) !important;
    }
    
    [data-testid="stChatInput"] textarea {
        background-color: white !important;
        color: #2D3748 !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 16px !important;
    }
    
    [data-testid="stChatInput"] textarea:focus {
        border: none !important;
        box-shadow: 0 0 0 3px rgba(0, 166, 147, 0.2) !important;
        outline: none !important;
    }
    
    /* Remove any decorative elements */
    [data-testid="stChatInput"] *::before,
    [data-testid="stChatInput"] *::after {
        display: none !important;
    }
    
    /* Style the send button - keep this nice */
    [data-testid="stChatInput"] button {
        background-color: #00A693 !important;
        color: white !important;
        border-radius: 50% !important;
        border: none !important;
        width: 48px !important;
        height: 48px !important;
    }
    
    [data-testid="stChatInput"] button:hover {
        background-color: #006B5B !important;
        transform: scale(1.05) !important;
        transition: all 0.2s ease !important;
    }
    
    /* Main title styling - keep this beautiful */
    h1 {
        color: #006B5B !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        text-align: center !important;
        padding: 20px 0 !important;
        border-bottom: 3px solid #00A693 !important;
        margin-bottom: 30px !important;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #00A693 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTION TO LOAD LOCAL CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- CRITICAL: PASTE YOUR INFO HERE ---
PROJECT_ID = "lumina-content-intelligence"
AGENT_ID = "39100170-63ca-4c8e-8c10-b8d6c1d1b55a"

# Function to connect to Dialogflow agent
def detect_intent_texts(text, session_id):
    location = "global"
    client_options = {"api_endpoint": f"{location}-dialogflow.googleapis.com"}
    
    try:
        credentials_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        session_client = dialogflow.SessionsClient(
            client_options=client_options, credentials=credentials
        )
        
        session_path = session_client.session_path(
            project=PROJECT_ID, location=location, agent=AGENT_ID, session=session_id
        )
        
        text_input = dialogflow.TextInput(text=text)
        query_input = dialogflow.QueryInput(text=text_input, language_code="en")

        request = dialogflow.DetectIntentRequest(
            session=session_path, 
            query_input=query_input
        )
        
        response = session_client.detect_intent(request=request)

        messages = []

        for msg in response.query_result.response_messages:
            try:
                if hasattr(msg, 'text') and msg.text:
                    for t in msg.text.text:
                        if t.strip():
                            messages.append({"type": "text", "content": t})
                elif hasattr(msg, 'payload') and msg.payload:
                    payload = dict(msg.payload)
                    messages.append({"type": "payload", "content": payload})
            except Exception as msg_error:
                continue

        return messages

    except Exception as e:
        st.error(f"An error occurred with Dialogflow: {e}")
        return []

# --- Streamlit User Interface ---
st.title("🚢 Welcome to SoundHopper")

# Inject CSS styling
inject_custom_css()
local_css("assets/style.css")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask your question about Washington State Ferries..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Thinking..."):
        agent_messages = detect_intent_texts(user_input, st.session_state.session_id)

    if agent_messages:
        for m in agent_messages:
            if m["type"] == "text":
                st.session_state.messages.append({"role": "assistant", "content": m["content"]})
                with st.chat_message("assistant"):
                    st.markdown(m["content"])
            elif m["type"] == "payload":
                payload = m["content"]
                with st.chat_message("assistant"):
                    if "buttons" in payload:
                        for btn in payload["buttons"]:
                            st.button(btn["label"])
                    if "image" in payload:
                        st.image(payload["image"]["url"], caption=payload["image"].get("caption", ""))