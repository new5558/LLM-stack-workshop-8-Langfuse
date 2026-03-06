# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Command to run the app
ENTRYPOINT ["streamlit", "run", "app_langfuse.py", "--server.port=8501", "--server.address=0.0.0.0"]
