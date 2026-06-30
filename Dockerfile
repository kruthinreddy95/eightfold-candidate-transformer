# Use official python slim image for minimal runtime container size
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install pinned dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files and mock data
COPY . .

# Default command to run the pipeline
CMD ["python", "-m", "src.main"]
