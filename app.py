import streamlit as st

st.set_page_config(layout="wide")

st.title("Washington State Ferries AI Assistant")

st.write("This is the future home of the SoundHopper RAG agent. This is a test to confirm the deployment process.")

# Placeholder for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response (placeholder)
    response = "This is a placeholder response. The full agent logic will be connected here."
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)