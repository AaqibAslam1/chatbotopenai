# Use the official Python image from the Docker Hub for the base stage
FROM python:3.11-slim AS base

# Set the timezone to ensure the date and time are correct
RUN apt-get update && apt-get install -y tzdata

# Install git and necessary build tools
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    build-essential \
    && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the required packages
RUN pip install --upgrade pip
RUN pip install --default-timeout=100 --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Stage for FastAPI
FROM base AS fastapi
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage for Streamlit
FROM base AS streamlit
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]