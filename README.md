# Workshop 8: Langfuse Monitoring & Observability

This workshop demonstrates how to integrate **Langfuse** into a Streamlit chatbot to track performance, security, and quality.

## Features
- ⚡ **Speed (Latency)**: Automatically tracked for every LLM call.
- 🎯 **Accuracy (Feedback)**: Integrated 👍/👎 buttons to score responses directly into Langfuse.
- 🛡️ **Security (Prompt Audit)**: Detects "weird" or suspicious prompts and tags them for review.
- 🪙 **Token Usage**: Detailed breakdown of input, output, and total tokens.


## 🐳 Running with Docker

You can also run the application using Docker Compose:

1. **Build and Start**:
   ```bash
   docker-compose up --build
   ```
2. **Access the app**:
   Open `http://localhost:8501` in your browser.


## How it works
- **Tracking**: We use the `langfuse.openai` wrapper for `openai.chat.completions.create`. This automatically captures traces, latency, and tokens.
- **Scoring**: The `langfuse.score` method is used to send user feedback back to the trace.
- **Audit**: A simple pattern matcher flags suspicious prompts, which are tagged as `suspicious` in Langfuse for easy filtering in the dashboard.
