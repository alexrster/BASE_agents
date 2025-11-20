FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Pillow
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY generate_grid_image.py .
COPY mcp_server.py .

# Make the server executable
RUN chmod +x mcp_server.py

# Set Python to unbuffered mode for better stdio handling
ENV PYTHONUNBUFFERED=1

# Run the MCP server
# Use -u flag for unbuffered output and ensure stdin is available
ENTRYPOINT ["python", "-u", "mcp_server.py"]

