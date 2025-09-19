import streamlit as st
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
import uuid
import base64
import requests
import time

# ---------- KEEP-ALIVE FUNCTIONALITY ----------
if "keepalive_ping" not in st.session_state:
    try:
        requests.get("https://wsf-chat.streamlit.app/", timeout=5)
        st.session_state.keepalive_ping = time.time()
    except:
        pass

# ---------- BRAND AVATARS with Ferry and User SVGs ----------
def svg_to_base64(svg_str):
    return "data:image/svg+xml;base64," + base64.b64encode(svg_str.encode("utf-8")).decode("utf-8")

user_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
<circle cx="32" cy="32" r="32" fill="#00A693"/>
<svg x="16" y="16" width="32" height="32" viewBox="0 0 640 640">
<path fill="white" d="M320 312C386.3 312 440 258.3 440 192C440 125.7 386.3 72 320 72C253.7 72 200 125.7 200 192C200 258.3 253.7 312 320 312zM290.3 368C191.8 368 112 447.8 112 546.3C112 562.7 125.3 576 141.7 576L498.3 576C514.7 576 528 562.7 528 546.3C528 447.8 448.2 368 349.7 368L290.3 368z"/>
</svg>
</svg>'''

assistant_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
<circle cx="32" cy="32" r="32" fill="#E0EFEC"/>
<svg x="16" y="16" width="32" height="32" viewBox="0 0 640 640">
<path fill="#006B5B" d="M224 96C224 78.3 238.3 64 256 64L384 64C401.7 64 416 78.3 416 96L416 128L464 128C508.2 128 544 163.8 544 208L544 336L543.9 336C544 336.7 544 337.3 544 338C544 368.2 536.4 397.8 522 424.3L509.3 447.6L508.7 448.6C486.4 437.3 462.2 431.8 437.9 431.9C405.4 432.1 373 442.6 345.5 463.3C323.4 479.9 316.4 479.9 294.3 463.3C266.2 442.2 233 431.7 199.9 431.9C176.3 432.1 152.8 437.6 131.2 448.6L130.6 447.6L117.9 424.3C103.5 397.8 95.9 368.1 95.9 338C95.9 337.3 95.9 336.6 96 336L95.9 336L95.9 208C95.9 163.8 131.7 128 175.9 128L223.9 128L223.9 96zM160 320L480 320L480 208C480 199.2 472.8 192 464 192L176 192C167.2 192 160 199.2 160 208L160 320z"/>
</svg>
</svg>'''

USER_AVATAR = svg_to_base64(user_svg)
ASSISTANT_AVATAR = svg_to_base64(assistant_svg)

# ---------- MINIMAL CSS - JUST CHAT STYLING ----------
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    .main, .stApp, html, body, [class*="css"] { font-family: 'Poppins', sans-serif !important; }

    /* Hide Streamlit branding */
    .main .block-container { padding-top: 0 !important; }
    
    /* More aggressive top spacing removal */
    .stApp {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    .main {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* Target the main container */
    .main > .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Try negative margins to pull content up */
    .main .block-container {
        margin-top: -20px !important;
    }

    /* Target any other containers */
    [data-testid="stVerticalBlock"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Chat message card */
    [data-testid="stChatMessage"]{
        background:#FFFFFF !important;
        border:1px solid #E0EFEC !important;
        border-radius:16px !important;
        padding:24px 32px !important;
        margin:-2px !important;  /* <-- Zero out all margins */
        box-shadow:none !important;
    }

    /* Text */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span{
    color:#000000 !important;
    font-family: 'Poppins', sans-serif !important;
    font-size:14px !important;
    line-height:1.4 !important;
    white-space:pre-wrap !important;
    margin:8px 0 !important;
}

    /* Lists */
    [data-testid="stChatMessage"] ul,
    [data-testid="stChatMessage"] ol{
        margin:12px 0 !important;
        padding-left:22px !important;
    }
    [data-testid="stChatMessage"] li{ margin:4px 0 !important; }

    /* Input */
    [data-testid="stChatInput"] > div{
        background:#FFFFFF !important;
        border:2px solid #00A693 !important;
        border-radius:30px !important;
        min-height:60px !important;
        padding:8px 16px !important;
        position: relative !important;
    }
    [data-testid="stChatInput"] textarea{
        background:#FFFFFF !important;
        color:#2D3748 !important;
        border:none !important;
        font-size:16px !important;
        padding:12px 16px !important;
    }
    [data-testid="stChatInput"] button{
        background:#00A693 !important;
        color:#FFFFFF !important;
        border:none !important;
        border-radius:50% !important;
        position:absolute !important;
        right:10px !important;
        top:50% !important;
        transform:translateY(-50%) !important;
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

        # This list will hold all our parsed messages (text and images)
        parsed_messages = []

        # First, check if we have session parameters (where your Cloud Function puts the data)
        session_params = {}
        if hasattr(response.query_result, 'parameters') and response.query_result.parameters:
            session_params = dict(response.query_result.parameters)

        # Check if we have an image URL in the session parameters
        if 'image_url' in session_params:
            image_url = session_params['image_url']
            parsed_messages.append({"role": "assistant", "type": "image", "content": image_url})

        # Then process regular text messages
        for msg in response.query_result.response_messages:
            # Case 1: The message is simple text
            if msg.text:
                for t in msg.text.text:
                    if t.strip():
                        parsed_messages.append({"role": "assistant", "type": "text", "content": t})

            # Case 2: Check payload as backup (in case richContent is used elsewhere)
            elif msg.payload:
                payload = dict(msg.payload)
                if 'richContent' in payload and payload['richContent']:
                    for rich_section in payload['richContent']:
                        for rich_item in rich_section:
                            if rich_item.get('type') == 'image':
                                image_url = rich_item.get('rawUrl')
                                if image_url:
                                    parsed_messages.append({"role": "assistant", "type": "image", "content": image_url})
                            elif rich_item.get('type') == 'text':
                                text_content = rich_item.get('text')
                                if text_content:
                                    parsed_messages.append({"role": "assistant", "type": "text", "content": text_content})
        
        return parsed_messages

    except Exception as e:
        st.error(f"An error occurred with Dialogflow: {e}")
        return [{"role": "assistant", "type": "text", "content": "Sorry, I'm having trouble connecting right now."}]

def reset_conversation():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = [
        {"role": "assistant", "type": "text", "content": "Welcome to SoundHopper from the Washington State Ferry System!\n\nI can help you find schedules, discover fares, make reservations, and help with questions about the ferry system.\n\nWhat can I help you with today?"}
    ]

# ---------- CLEAN CHAT INTERFACE ONLY ----------
inject_custom_css()

if st.query_params.get("reset") == "true":
    reset_conversation()
    st.query_params.clear()
    st.rerun()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "type": "text", "content": "Welcome to SoundHopper from the Washington State Ferry System!\n\nI can help you find schedules, discover fares, make reservations, and help with questions about the ferry system.\n\nWhat can I help you with today?"}
    ]

# Display chat history
for message in st.session_state.messages:
    role = message["role"]
    avatar = USER_AVATAR if role == "user" else ASSISTANT_AVATAR
    with st.chat_message(role, avatar=avatar):
        
        # Check the "type" of the message to decide how to render it
        message_type = message.get("type", "text") # Default to text if type isn't specified

        if message_type == "image":
            st.image(message["content"], width=400, caption="Ferry Terminal")
        else: # This handles "text" and any older messages without a type
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What can I help you with?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    
    # Get response from Dialogflow
    with st.spinner("Thinking..."):
        agent_messages = detect_intent_texts(prompt, st.session_state.session_id)

    # Add all of the agent's messages (could be images, text, etc.) to history
    for msg in agent_messages:
        st.session_state.messages.append(msg)
    
    # Rerun the app to display the new messages
    st.rerun()