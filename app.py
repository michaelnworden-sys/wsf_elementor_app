import streamlit as st
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
import uuid
import json

# --- FUNCTION TO LOAD LOCAL CSS ---
# This function will read your CSS file and apply it to the app.
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- CRITICAL: PASTE YOUR INFO HERE ---
PROJECT_ID = "lumina-content-intelligence"
AGENT_ID = "39100170-63ca-4c8e-8c10-b8d6c1d1b55a"

# --- DO NOT EDIT BELOW THIS LINE ---

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

        # --- THIS IS THE FIX ---
        # 1. Create a config that specifies NO audio output
        audio_config = dialogflow.OutputAudioConfig(
            audio_encoding=dialogflow.OutputAudioEncoding.OUTPUT_AUDIO_ENCODING_UNSPECIFIED
        )
        
        # 2. Add the query_input AND the new audio_config to the request
        request = dialogflow.DetectIntentRequest(
            session=session_path, 
            query_input=query_input,
            output_audio_config=audio_config, # <-- ADD THIS LINE
        )
        # --- END OF FIX ---

        response = session_client.detect_intent(request=request)

        messages = []

        # This part of your code is perfect and doesn't need to change
        for msg in response.query_result.response_messages:
            if msg.text:
                for t in msg.text.text:
                    if t.strip():
                        messages.append({"type": "text", "content": t})

            elif msg.payload:
                payload = dict(msg.payload)
                messages.append({"type": "payload", "content": payload})

            # Even though you have code to handle audio, the error happens
            # before this code is ever reached. The fix above prevents the
            # 'output_audio' field from being sent in the first place.
            elif msg.output_audio:
                messages.append({"type": "audio", "content": msg.output_audio})

            else:
                messages.append({"type": "unknown", "content": str(msg)})

        return messages

    except Exception as e:
        # The error message here is what you're seeing on the screen
        st.error(f"An error occurred with Dialogflow: {e}")
        return []


# --- Streamlit User Interface ---
st.title("Welcome to SoundHopper")

# --- APPLY THE CUSTOM CSS ---
local_css("assets/style.css")

# Initialize chat history and session ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# ... (the rest of your UI code remains exactly the same) ...

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get new user input
if user_input := st.chat_input("Ask your question:"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("Thinking..."):
        agent_messages = detect_intent_texts(user_input, st.session_state.session_id)

    # Show agent messages
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

            elif m["type"] == "audio":
                with st.chat_message("assistant"):
                    st.audio(m["content"], format="audio/wav")

            else:
                with st.chat_message("assistant"):
                    st.write("⚠️ Unhandled response:", m["content"])
