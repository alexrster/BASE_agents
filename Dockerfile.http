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
COPY mcp_http_server.py .

# Make the server executable
RUN chmod +x mcp_http_server.py

# Set Python to unbuffered mode for better output handling
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

# Expose HTTP port
EXPOSE 8000

# Run the HTTP MCP server
CMD ["python", "-u", "mcp_http_server.py"]

