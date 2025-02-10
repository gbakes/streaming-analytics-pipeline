FROM python:3.9-slim

# Set working directory
WORKDIR /opt/dagster/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create dagster home directory
RUN mkdir -p /opt/dagster/dagster_home

# Set environment variables
ENV DAGSTER_HOME=/opt/dagster/dagster_home
ENV PYTHONPATH=/opt/dagster/app

# Copy dagster instance configuration
COPY dagster.yaml /opt/dagster/dagster_home/

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .
