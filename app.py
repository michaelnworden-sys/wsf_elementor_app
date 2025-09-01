import streamlit as st
from google.cloud import dialogflowcx_v3 as dialogflow
from google.oauth2 import service_account
import uuid
import base64

# ---------- BRAND AVATARS (data-URL SVGs) ----------
def make_avatar_data_url(bg="#00A693", fg="#FFFFFF", label="U"):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
<defs><style>
text {{ font-family: Arial, Helvetica, sans-serif; font-weight:700; }}
</style></defs>
<circle cx="32" cy="32" r="32" fill="{bg}"/>
<text x="50%" y="50%" dy="10" text-anchor="middle" font-size="32" fill="{fg}">{label}</text>
</svg>'''
    data = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{data}"

USER_AVATAR      = make_avatar_data_url(bg="#00A693", fg="#FFFFFF", label="U")      # teal with white
ASSISTANT_AVATAR = make_avatar_data_url(bg="#E0EFEC", fg="#006B5B", label="AI")    # light teal with dark teal

# ---------- CSS (formatting only; no avatar hacks) ----------
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    .main, .stApp, html, body, [class*="css"] { font-family: 'Poppins', sans-serif !important; }

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

# replay history with custom avatars
for message in st.session_state.messages:
    role = message["role"]
    avatar = USER_AVATAR if role == "user" else ASSISTANT_AVATAR
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

prompt = st.chat_input("Ask your question about Washington State Ferries...")
if prompt:
    # echo user with custom avatar
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        agent_messages = detect_intent_texts(prompt, st.session_state.session_id)

    if agent_messages:
        for m in agent_messages:
            if m["type"] == "text":
                st.session_state.messages.append({"role": "assistant", "content": m["content"]})
                with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                    st.markdown(m["content"])
            elif m["type"] == "payload":
                payload = m["content"]
                with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                    if "buttons" in payload:
                        for btn in payload["buttons"]:
                            st.button(btn["label"])
                    if "image" in payload:
                        st.image(payload["image"]["url"], caption=payload["image"].get("caption", ""))
