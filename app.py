import streamlit as st
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
import uuid
import base64

# Set the page layout to "wide". This should be the first Streamlit command.
st.set_page_config(layout="wide")

# ---------- BRAND AVATARS with Ferry and User SVGs ----------
def svg_to_base64(svg_str):
    return "data:image/svg+xml;base64," + base64.b64encode(svg_str.encode("utf-8")).decode("utf-8")

# User avatar: teal background with white user icon
user_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
<circle cx="32" cy="32" r="32" fill="#00A693"/>
<svg x="16" y="16" width="32" height="32" viewBox="0 0 640 640">
<path fill="white" d="M320 312C386.3 312 440 258.3 440 192C440 125.7 386.3 72 320 72C253.7 72 200 125.7 200 192C200 258.3 253.7 312 320 312zM290.3 368C191.8 368 112 447.8 112 546.3C112 562.7 125.3 576 141.7 576L498.3 576C514.7 576 528 562.7 528 546.3C528 447.8 448.2 368 349.7 368L290.3 368z"/>
</svg>
</svg>'''

# Assistant avatar: light teal background with dark green ferry icon
assistant_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
<circle cx="32" cy="32" r="32" fill="#E0EFEC"/>
<svg x="16" y="16" width="32" height="32" viewBox="0 0 640 640">
<path fill="#006B5B" d="M224 96C224 78.3 238.3 64 256 64L384 64C401.7 64 416 78.3 416 96L416 128L464 128C508.2 128 544 163.8 544 208L544 336L543.9 336C544 336.7 544 337.3 544 338C544 368.2 536.4 397.8 522 424.3L509.3 447.6L508.7 448.6C486.4 437.3 462.2 431.8 437.9 431.9C405.4 432.1 373 442.6 345.5 463.3C323.4 479.9 316.4 479.9 294.3 463.3C266.2 442.2 233 431.7 199.9 431.9C176.3 432.1 152.8 437.6 131.2 448.6L130.6 447.6L117.9 424.3C103.5 397.8 95.9 368.1 95.9 338C95.9 337.3 95.9 336.6 96 336L95.9 336L95.9 208C95.9 163.8 131.7 128 175.9 128L223.9 128L223.9 96zM160 320L480 320L480 208C480 199.2 472.8 192 464 192L176 192C167.2 192 160 199.2 160 208L160 320z"/>
</svg>
</svg>'''

USER_AVATAR = svg_to_base64(user_svg)
ASSISTANT_AVATAR = svg_to_base64(assistant_svg)

# ---------- CSS (formatting + STICKY MAP RULE) ----------
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    .main, .stApp, html, body, [class*="css"] { font-family: 'Poppins', sans-serif !important; }

    /* Makes the map column sticky */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        position: sticky;
        top: 2rem;
    }

    /* Chat message card styling */
    [data-testid="stChatMessage"]{
        background:#FFFFFF !important; border:1px solid #E0EFEC !important;
        border-radius:16px !important; padding:24px 32px !important;
        margin:8px 0 !important; box-shadow:none !important;
    }
    
    /* Input bar styling */
    [data-testid="stChatInput"] > div{
        background:#FFFFFF !important; border:2px solid #00A693 !important;
        border-radius:30px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------- Dialogflow CX ----------
PROJECT_ID = "lumina-content-intelligence"
AGENT_ID   = "39100170-63ca-4c8e-8c10-b8d6c1d1b55a"

def detect_intent_texts(text, session_id):
    location = "global"
    client_options = {"api_endpoint": f"{location}-dialogflow.googleapis.com"}
    try:
        credentials_info = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        session_client = dialogflow.SessionsClient(client_options=client_options, credentials=credentials)
        session_path = session_client.session_path(project=PROJECT_ID, location=location, agent=AGENT_ID, session=session_id)
        text_input = dialogflow.TextInput(text=text)
        query_input = dialogflow.QueryInput(text=text_input, language_code="en")
        request = dialogflow.DetectIntentRequest(session=session_path, query_input=query_input)
        response = session_client.detect_intent(request=request)
        messages = []
        for msg in response.query_result.response_messages:
            try:
                if hasattr(msg, 'text') and msg.text:
                    for t in msg.text.text:
                        if t.strip(): messages.append({"type": "text", "content": t})
                elif hasattr(msg, 'payload') and msg.payload:
                    messages.append({"type": "payload", "content": dict(msg.payload)})
            except Exception: continue
        return messages
    except Exception as e:
        st.error(f"An error occurred with Dialogflow: {e}")
        return []

# ---------- UI ----------
# The header remains full-width at the top
st.markdown("""
<div style="display:flex; align-items:center; justify-content:center; gap:15px; color:#006B5B; font-family:'Poppins', sans-serif; font-weight:700; text-align:center; padding:20px 0; border-bottom:3px solid #00A693; margin-bottom:30px;">
  <img src="https://storage.googleapis.com/ferry_data/NewWSF/ferryimages/200px-Washington_State_Department_of_Transportation_Logo.png" style="height:4em; width:auto;">
  <h1 style="margin:0; color:#006B5B;">Welcome to SoundHopper</h1>
</div>
""", unsafe_allow_html=True)

inject_custom_css()

# We use the three-column layout again for reliable centering
left_spacer, main_content, right_spacer = st.columns([1, 5, 1])

with main_content:
    # Create the two columns for chat and map
    chat_col, map_col = st.columns([3, 2], gap="large")

    with chat_col:
        # --- THE KEY FIX ---
        # 1. We create the chat history container with a shorter height to prevent page scrolling.
        #    Adjust this value (e.g., 500, 550, 600) to best fit your screen.
        chat_history_container = st.container(height=550, border=False)
        with chat_history_container:
            if "session_id" not in st.session_state:
                st.session_state.session_id = str(uuid.uuid4())
            if "messages" not in st.session_state:
                st.session_state.messages = []
            
            # Display past messages
            for message in st.session_state.messages:
                role = message["role"]
                avatar = USER_AVATAR if role == "user" else ASSISTANT_AVATAR
                with st.chat_message(role, avatar=avatar):
                    st.markdown(message["content"])

        # 2. The chat input is placed *inside* the chat column but *outside* the history container.
        #    This correctly pins it to the bottom of the column.
        if prompt := st.chat_input("Ask your question about Washington State Ferries..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Thinking..."):
                agent_messages = detect_intent_texts(prompt, st.session_state.session_id)
            if agent_messages:
                for m in agent_messages:
                    if m["type"] == "text":
                        st.session_state.messages.append({"role": "assistant", "content": m["content"]})
            st.rerun()

    with map_col:
        st.image(
            "https://storage.googleapis.com/ferry_data/NewWSF/ferryimages/Route%20Map.png",
            use_container_width=True
        )