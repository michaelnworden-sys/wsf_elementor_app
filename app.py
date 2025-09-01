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
    
    /* Apply Poppins font */
    .main, .stApp, html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* NUCLEAR OPTION - Override everything inside chat messages */
    [data-testid="stChatMessage"] {
        background-color: white !important;
        border: 1px solid #E0EFEC !important;
        border-radius: 16px !important;
        box-shadow: none !important;
        padding: 24px 32px !important;
        margin: 8px 0 !important;
    }

    /* Kill ALL backgrounds inside chat messages except avatars */
    [data-testid="stChatMessage"] > div > div:not([data-testid*="stChatMessageAvatar"]) {
        background: white !important;
        background-color: white !important;
        background-image: none !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Target the actual content container that holds the text */
    [data-testid="stChatMessage"] > div > div:last-child,
    [data-testid="stChatMessage"] > div > div:last-child > div,
    [data-testid="stChatMessage"] > div > div:last-child > div > div {
        background: white !important;
        background-color: white !important;
        background-image: none !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Force all text elements to have no background */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] div p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div span {
        background: white !important;
        background-color: white !important;
        color: black !important;
        font-size: 16px !important;
        font-family: 'Poppins', sans-serif !important;
        line-height: 1.6 !important;
        white-space: pre-wrap !important;
        margin: 8px 0 !important;
        padding: 0 !important;
        border: none !important;
    }

    /* Lists */
    [data-testid="stChatMessage"] ul,
    [data-testid="stChatMessage"] ol {
        background: white !important;
        background-color: white !important;
        margin: 12px 0 !important;
        padding-left: 20px !important;
    }

    [data-testid="stChatMessage"] li {
        background: white !important;
        background-color: white !important;
        color: black !important;
        margin: 4px 0 !important;
        padding: 0 !important;
        border: none !important;
    }

    /* User avatar - teal green with white icon */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageAvatarUser"] > div {
        background-color: #00A693 !important;
        color: white !important;
        border-radius: 12px !important;
    }
    
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) svg {
        color: white !important;
        fill: white !important;
    }

    /* Assistant avatar - light teal with dark teal icon */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageAvatarAssistant"] > div {
        background-color: #E0EFEC !important;
        color: #006B5B !important;
        border-radius: 12px !important;
    }
    
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) svg {
        color: #006B5B !important;
        fill: #006B5B !important;
    }

    /* Custom logo styling */
    .logo-title {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 15px !important;
    }

    .logo-title img {
        height: 1.2em !important;
        width: auto !important;
    }

    /* Input box styling */
    [data-testid="stChatInput"] > div {
        background-color: white !important;
        border: 2px solid #00A693 !important;
        border-radius: 30px !important;
        min-height: 60px !important;
        padding: 8px 16px !important;
    }

    [data-testid="stChatInput"] textarea {
        background-color: white !important;
        color: #2D3748 !important;
        border: none !important;
        font-size: 16px !important;
        min-height: 30px !important;
        padding: 12px 16px !important;
    }
    
    [data-testid="stChatInput"] button {
        background-color: #00A693 !important;
        color: white !important;
        border-radius: 50% !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: auto !important;
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
st.markdown("""
<div style="display: flex; align-items: center; justify-content: center; gap: 15px; color: #006B5B; font-family: 'Poppins', sans-serif; font-weight: 700; text-align: center; padding: 20px 0; border-bottom: 3px solid #00A693; margin-bottom: 30px;">
    <img src="https://storage.googleapis.com/ferry_data/NewWSF/ferryimages/200px-Washington_State_Department_of_Transportation_Logo.png" style="height: 4em; width: auto;">
    <h1 style="margin: 0; color: #006B5B;">Welcome to SoundHopper</h1>
</div>
""", unsafe_allow_html=True)

# Inject CSS styling
inject_custom_css()
#local_css("assets/style.css")

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