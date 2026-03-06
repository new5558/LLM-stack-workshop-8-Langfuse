import os
import streamlit as st
from langfuse.openai import openai
from langfuse import Langfuse
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")

# Configure Langfuse-wrapped OpenAI client
openai.api_key = GROQ_API_KEY
openai.base_url = "https://api.groq.com/openai/v1/"

# Initialize Langfuse client for manual scoring
langfuse = Langfuse()

st.set_page_config(page_title="Workshop 8: Langfuse Chatbot", page_icon="🚀")

st.title("🤖 Workshop 8: Langfuse Monitoring")

# Session management
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


# Helper: Detect unusual prompts
def audit_prompt(prompt):
    suspicious_patterns = [
        "ignore previous",
        "system prompt",
        "jailbreak",
        "base64",
        "sql injection",
    ]
    for pattern in suspicious_patterns:
        if pattern in prompt.lower():
            return True
    return False


# Display Chat History
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Feedback mechanism for Assistant messages
        if msg["role"] == "assistant" and "trace_id" in msg:
            col1, col2, _ = st.columns([0.15, 0.15, 0.7])
            trace_id = msg["trace_id"]

            # Using unique keys for each button
            if col1.button("👍", key=f"up_{trace_id}_{i}"):
                langfuse.score(
                    trace_id=trace_id,
                    name="user-feedback",
                    value=1,
                    comment="User liked the response",
                )
                st.toast("Feedback sent: Positive")

            if col2.button("👎", key=f"down_{trace_id}_{i}"):
                langfuse.score(
                    trace_id=trace_id,
                    name="user-feedback",
                    value=0,
                    comment="User disliked the response",
                )
                st.toast("Feedback sent: Negative")

# Chat Input
if prompt := st.chat_input("Ask anything..."):
    # 1. Audit prompt for "แปลกๆ" (weird/suspicious)
    is_suspicious = audit_prompt(prompt)

    # 2. Store and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 3. Call LLM with Langfuse tracking
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Use Langfuse's wrapped OpenAI client for automatic tracking
                # It tracks: Latency (Speed) and Tokens (Usage)
                response = openai.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    name="Workshop-8-Chat",
                )

                answer = response.choices[0].message.content

                st.markdown(answer)

                # Add to history
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

                if is_suspicious:
                    st.warning("⚠️ Security Alert: This prompt was flagged as unusual.")

            except Exception as e:
                st.error(f"Error: {e}")
