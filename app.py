import streamlit as st
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
import uuid
import base64

# Set page to wide layout
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

# ---------- CSS with FOCUSED CENTERED LAYOUT ----------
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    .main, .stApp, html, body, [class*="css"] { font-family: 'Poppins', sans-serif !important; }

    /* Focused center layout - not full width */
    .main .block-container {
        max-width: 1400px !important;
        padding-left: 5% !important;
        padding-right: 5% !important;
    }

    /* Chat column - align content to the right with gap */
    [data-testid="column"]:first-child {
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-end !important;
        padding-right: 2.5% !important;
    }

    /* Map column - align content to the left with gap */
    [data-testid="column"]:last-child {
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        padding-left: 2.5% !important;
    }

    /* Chat container - limit width */
    [data-testid="column"]:first-child > div {
        width: 100% !important;
        max-width: 600px !important;
    }

    /* Map container - limit width and center the image */
    [data-testid="column"]:last-child > div {
        width: 100% !important;
        max-width: 500px !important;
    }

    /* Chat message card */
    [data-testid="stChatMessage"]{
        background:#FFFFFF !important;
        border:1px solid #E0EFEC !important;
        border-radius:16px !important;
        padding:24px 32px !important;
        margin:8px 0 !important;
        box-shadow:none !important;
    }

    /* Text */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span{
        color:#000000 !important;
        font-size:16px !important;
        line-height:1.6 !important;
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

    /* Mobile responsive */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        [data-testid="column"]:first-child,
        [data-testid="column"]:last-child {
            align-items: center !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
        
        [data-testid="column"]:first-child > div,
        [data-testid="column"]:last-child > div {
            max-width: 100% !important;
        }
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
                        if t.strip():
                            messages.append({"type": "text", "content": t})
                elif hasattr(msg, 'payload') and msg.payload:
                    payload = dict(msg.payload)
                    messages.append({"type": "payload", "content": payload})
            except Exception:
                continue
        return messages

    except Exception as e:
        st.error(f"An error occurred with Dialogflow: {e}")
        return []

# ---------- UI ----------
st.markdown("""
<div style="display:flex; align-items:center; justify-content:center; gap:15px; color:#006B5B; font-family:'Poppins', sans-serif; font-weight:700; text-align:center; padding:20px 0; border-bottom:3px solid #00A693; margin-bottom:30px;">
  <img src="https://storage.googleapis.com/ferry_data/NewWSF/ferryimages/200px-Washington_State_Department_of_Transportation_Logo.png" style="height:4em; width:auto;">
  <h1 style="margin:0; color:#006B5B;">Welcome to SoundHopper</h1>
</div>
""", unsafe_allow_html=True)

inject_custom_css()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create two columns with equal width
chat_col, map_col = st.columns([1, 1])

with chat_col:
    # Chat history in a container
    chat_container = st.container(height=600, border=False)
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            avatar = USER_AVATAR if role == "user" else ASSISTANT_AVATAR
            with st.chat_message(role, avatar=avatar):
                st.markdown(message["content"])

    # Chat input outside the container
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
    st.markdown("""
    <div style="width: 100%; height: 600px; display: flex; align-items: center; justify-content: center;">
        <img src="https://storage.googleapis.com/ferry_data/NewWSF/ferryimages/Route%20Map.png" 
             style="max-width: 100%; max-height: 100%; object-fit: contain;" />
    </div>
    """, unsafe_allow_html=True)