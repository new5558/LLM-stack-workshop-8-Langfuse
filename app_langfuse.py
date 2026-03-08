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

if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = True  # Allow first question

# Generate deterministic trace ID from session ID for distributed tracing
if "trace_id" not in st.session_state:
    st.session_state.trace_id = langfuse.create_trace_id(
        seed=st.session_state.session_id
    )


# LLM-as-a-Judge: Evaluate response quality using an LLM
def evaluate_response_with_llm(user_prompt, assistant_response, trace_id):
    """
    Use an LLM as a judge to evaluate the quality of the assistant's response.
    Scores the response based on helpfulness, accuracy, relevance, and clarity.

    Reference: https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge
    """
    evaluation_prompt = f"""You are an expert evaluator. Evaluate the following response from an AI assistant.

User Query: {user_prompt}

Assistant Response: {assistant_response}

Provide a structured evaluation:
1. Helpfulness [1-5]: How well does the response help the user?
2. Accuracy [1-5]: Is the information factually correct?
3. Relevance [1-5]: Does the response address the query?
4. Clarity [1-5]: Is the response clear and well-structured?

Provide your evaluation in this exact format:
HELPFULNESS: [score] [brief reason]
ACCURACY: [score] [brief reason]
RELEVANCE: [score] [brief reason]
CLARITY: [score] [brief reason]
OVERALL: [average score rounded to 1 decimal]"""

    # Call LLM for evaluation
    evaluation_response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": evaluation_prompt}],
        name="LLM-as-Judge-Evaluator",
        trace_id=trace_id,
    )

    evaluation_text = evaluation_response.choices[0].message.content

    # Parse evaluation scores
    lines = evaluation_text.split("\n")
    scores = {}
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key in ["HELPFULNESS", "ACCURACY", "RELEVANCE", "CLARITY"]:
                score = float(value.split()[0])
                scores[key.lower()] = score
            elif key == "OVERALL":
                score = float(value.split()[0])
                scores["overall"] = score

    # Create scores in Langfuse for tracking
    if scores:
        for score_name, score_value in scores.items():
            langfuse.create_score(
                trace_id=trace_id,
                name=f"llm-judge-{score_name}",
                value=score_value,
                comment=f"LLM-as-Judge evaluation: {score_name}",
            )

    return evaluation_text, scores


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
                langfuse.create_score(
                    trace_id=trace_id,
                    name="user-feedback",
                    value=1,
                    comment="User liked the response",
                )
                st.toast("Feedback sent: Positive ✓")
                st.session_state.feedback_given = True
                st.rerun()

            if col2.button("👎", key=f"down_{trace_id}_{i}"):
                langfuse.create_score(
                    trace_id=trace_id,
                    name="user-feedback",
                    value=0,
                    comment="User disliked the response",
                )
                st.toast("Feedback sent: Negative ✓")
                st.session_state.feedback_given = True
                st.rerun()

# Chat Input
if prompt := st.chat_input("Ask anything..."):
    # Store and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call LLM with Langfuse tracking
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Use Langfuse's wrapped OpenAI client for automatic tracking
            # It tracks: Latency (Speed) and Tokens (Usage)
            response = openai.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                name="Workshop-8-Chat",
                trace_id=st.session_state.trace_id,
            )

            answer = response.choices[0].message.content

            st.markdown(answer)

            # Display trace ID for this response
            # st.caption(f"🔗 Trace ID: `{st.session_state.trace_id}`")

            # LLM-as-a-Judge: Evaluate the response quality
            with st.spinner("🤔 Running LLM-as-Judge evaluation..."):
                evaluation_text, scores = evaluate_response_with_llm(
                    prompt, answer, st.session_state.trace_id
                )

            if evaluation_text:
                with st.expander("📊 LLM-as-Judge Evaluation"):
                    st.markdown(evaluation_text)
                    if scores:
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric(
                                "Helpfulness",
                                f"{scores.get('helpfulness', 0):.1f}/5.0",
                            )
                        with col2:
                            st.metric(
                                "Accuracy", f"{scores.get('accuracy', 0):.1f}/5.0"
                            )
                        with col3:
                            st.metric(
                                "Relevance", f"{scores.get('relevance', 0):.1f}/5.0"
                            )
                        with col4:
                            st.metric("Clarity", f"{scores.get('clarity', 0):.1f}/5.0")
                        with col5:
                            st.metric("Overall", f"{scores.get('overall', 0):.1f}/5.0")

            # Add to history with trace ID for reference
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "trace_id": st.session_state.trace_id,
                }
            )
