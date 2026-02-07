# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements file first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ ./src/

# Set the entrypoint to run the analyzer script
ENTRYPOINT ["python", "src/analyze.py"]

# Default command shows help if no arguments provided
CMD ["--help"]
