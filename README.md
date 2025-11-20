# Electricity Grid Availability Image Generator - MCP Server

[![CI](https://github.com/alexrster/BASE_agents/workflows/CI/badge.svg)](https://github.com/alexrster/BASE_agents/actions/workflows/ci.yml)
[![Docker Build](https://github.com/alexrster/BASE_agents/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)](https://github.com/alexrster/BASE_agents/actions/workflows/docker-build.yml)

This project provides an MCP (Model Context Protocol) server that generates visualizations of electricity grid availability.

## Features

- Generates 1024x250px images showing 24-hour grid availability
- iOS-style design with SF Pro fonts and system colors
- Supports availability states: available (●), unavailable (✕), partial (%), and unknown (-)
- Shows current time marker when viewing today's date

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### As an MCP Server

Run the MCP server:

```bash
python mcp_server.py
```

The server exposes one tool: `generate_grid_availability_image`

### Tool Parameters

- `grid_data` (required): JSON object containing:
  - `T_Date`: Date in DD-MM-YYYY format (e.g., "20-11-2025")
  - `T_00` through `T_23`: State for each hour (0-23)
    - `●`: Available
    - `✕`: Unavailable
    - `%`: Partial/transition
    - `-`: Unknown

- `output_path` (optional): File path to save the image. If not provided, a temporary file is used.

- `return_base64` (optional, default: false): If true, returns the image as base64-encoded data.

### Example Usage

```python
# Example grid data
grid_data = {
    "T_Date": "20-11-2025",
    "T_00": "●", "T_01": "●", "T_02": "●", "T_03": "●",
    "T_04": "●", "T_05": "●", "T_06": "✕", "T_07": "✕",
    "T_08": "✕", "T_09": "✕", "T_10": "✕", "T_11": "✕",
    "T_12": "✕", "T_13": "●", "T_14": "●", "T_15": "●",
    "T_16": "%", "T_17": "✕", "T_18": "✕", "T_19": "✕",
    "T_20": "✕", "T_21": "✕", "T_22": "✕", "T_23": "%"
}
```

### Standalone Script

You can also use the original script directly:

```bash
# Using example data
python generate_grid_image.py

# Using JSON file
python generate_grid_image.py data.json

# Using stdin
echo '{"T_Date": "20-11-2025", "T_00": "●", ...}' | python generate_grid_image.py -

# Specify output path
python generate_grid_image.py data.json output.png
```

## Docker Deployment

### Building the Docker Image

```bash
docker build -t grid-image-generator .
```

### Running with Docker

For stdio-based MCP communication (recommended for MCP clients):

```bash
docker run -i --rm grid-image-generator
```

The `-i` flag keeps stdin open, which is required for MCP stdio communication.

### Running with Docker Compose

For development or testing:

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# To interact with it via stdio
docker exec -i grid-image-generator-mcp python mcp_server.py

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Output Directory

The Docker setup includes a volume mount for output files. Generated images will be saved to the `./output` directory on your host machine (mounted at `/app/output` in the container).

## MCP Configuration

### Local Installation

To use this MCP server with a client, add it to your MCP configuration file:

```json
{
  "mcpServers": {
    "grid-image-generator": {
      "command": "python",
      "args": ["/path/to/BASE_agents/mcp_server.py"]
    }
  }
}
```

### Docker Installation

For Docker-based deployment, configure your MCP client to use Docker:

**Option 1: Direct Docker run (Recommended)**

```json
{
  "mcpServers": {
    "grid-image-generator": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "grid-image-generator"
      ]
    }
  }
}
```

**Option 2: Using docker-compose**

First, ensure the container is running:
```bash
docker-compose up -d
```

Then configure:
```json
{
  "mcpServers": {
    "grid-image-generator": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "grid-image-generator-mcp",
        "python",
        "mcp_server.py"
      ]
    }
  }
}
```

**Option 3: Using the build script**

```bash
./build.sh
```

Then use Option 1 configuration above.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

### CI Pipeline

The CI pipeline (`ci.yml`) runs on every push and pull request:
- Lints Python code with flake8
- Checks Python syntax
- Tests MCP server imports
- Tests image generation functionality

### Docker Build Pipeline

The Docker build pipeline (`docker-build.yml`) automatically:
- Builds Docker images for multiple platforms (linux/amd64, linux/arm64)
- Pushes images to GitHub Container Registry (ghcr.io)
- Tags images with branch names, commit SHAs, and semantic versions
- Uses Docker layer caching for faster builds

### Release Pipeline

The release pipeline (`release.yml`) runs when:
- A new GitHub release is published
- Manually triggered via workflow_dispatch

It builds and pushes versioned Docker images to the container registry.

### Using Pre-built Images

You can use the pre-built Docker images from GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/alexrster/BASE_agents:latest

# Or use a specific version
docker pull ghcr.io/alexrster/BASE_agents:v1.0.0
```

Replace `alexrster` with your GitHub username or organization name.

### Workflow Status

Check the [Actions tab](https://github.com/alexrster/BASE_agents/actions) in your repository to view workflow runs and their status.

## n8n Integration

This MCP server can be integrated into n8n workflows using the HTTP API wrapper. 

> **📖 For detailed n8n integration instructions, see [N8N_INTEGRATION.md](N8N_INTEGRATION.md)**

Here's a quick overview:

### Option 1: Using HTTP Server (Recommended for n8n)

The HTTP server provides a REST API that n8n can easily consume.

#### 1. Start the HTTP Server

**Using Docker:**
```bash
# Build the HTTP server image
docker build -f Dockerfile.http -t grid-image-generator-http .

# Run the HTTP server
docker run -d -p 8000:8000 --name grid-image-generator-http grid-image-generator-http
```

**Using Python directly:**
```bash
pip install -r requirements.txt
python mcp_http_server.py
```

The server will be available at `http://localhost:8000`

#### 2. Configure n8n HTTP Request Node

In your n8n workflow:

1. **Add an HTTP Request Node**
   - Method: `POST`
   - URL: `http://localhost:8000/tools/generate_grid_availability_image`
   - (Or use the simplified endpoint: `http://localhost:8000/generate`)

2. **Set Headers:**
   ```
   Content-Type: application/json
   ```

3. **Set Body (JSON):**
   ```json
   {
     "grid_data": {
       "T_Date": "20-11-2025",
       "T_00": "●",
       "T_01": "●",
       "T_02": "●",
       "T_03": "●",
       "T_04": "●",
       "T_05": "●",
       "T_06": "✕",
       "T_07": "✕",
       "T_08": "✕",
       "T_09": "✕",
       "T_10": "✕",
       "T_11": "✕",
       "T_12": "✕",
       "T_13": "●",
       "T_14": "●",
       "T_15": "●",
       "T_16": "%",
       "T_17": "✕",
       "T_18": "✕",
       "T_19": "✕",
       "T_20": "✕",
       "T_21": "✕",
       "T_22": "✕",
       "T_23": "%"
     },
     "return_base64": true
   }
   ```

4. **Response Handling:**
   - If `return_base64: true`: The response will contain `image_base64` field
   - If `return_base64: false`: The response will be a PNG image binary

#### 3. Example n8n Workflow

```
[Webhook] → [HTTP Request] → [Save File] or [Send Email]
```

**HTTP Request Node Configuration:**
- **Method:** POST
- **URL:** `http://localhost:8000/generate`
- **Body Content Type:** JSON
- **Body:** Use expression editor to build the JSON from previous node data

**Example Expression for Body:**
```javascript
{
  "grid_data": {
    "T_Date": "{{ $json.date }}",
    "T_00": "{{ $json.hour_00 }}",
    "T_01": "{{ $json.hour_01 }}",
    // ... add all hours
  },
  "return_base64": false
}
```

#### 4. Using Base64 Response

If you set `return_base64: true`, you can:
- Save the base64 string to a file using n8n's Write Binary File node
- Send it as an attachment in emails
- Display it in webhooks or APIs

**Example: Convert Base64 to Binary File**
```javascript
// In a Function node after HTTP Request
const base64Data = $input.item.json.image_base64;
const buffer = Buffer.from(base64Data, 'base64');
return [{ json: {}, binary: { data: buffer } }];
```

### Option 2: Using n8n MCP Client Tool (If Available)

If your n8n instance supports MCP Client Tool nodes:

1. **Add MCP Client Tool Node**
2. **Configure:**
   - **SSE Endpoint:** `http://localhost:8000` (if using HTTP wrapper)
   - Or use stdio: `docker run -i --rm grid-image-generator`
3. **Select Tool:** `generate_grid_availability_image`
4. **Map Inputs:** Connect your data to the tool inputs

### API Endpoints

The HTTP server provides the following endpoints:

- `GET /` - API information
- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /tools/generate_grid_availability_image` - Generate image (full MCP-compatible)
- `POST /generate` - Generate image (simplified endpoint)

### Docker Compose for HTTP Server

Create a `docker-compose.http.yml`:

```yaml
version: '3.8'

services:
  grid-image-generator-http:
    build:
      context: .
      dockerfile: Dockerfile.http
    container_name: grid-image-generator-http
    ports:
      - "8000:8000"
    volumes:
      - ./output:/app/output
    environment:
      - PYTHONUNBUFFERED=1
      - PORT=8000
      - HOST=0.0.0.0
    restart: unless-stopped
```

Run with:
```bash
docker-compose -f docker-compose.http.yml up -d
```

### Testing the API

Test the API with curl:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "grid_data": {
      "T_Date": "20-11-2025",
      "T_00": "●", "T_01": "●", "T_02": "●", "T_03": "●",
      "T_04": "●", "T_05": "●", "T_06": "✕", "T_07": "✕",
      "T_08": "✕", "T_09": "✕", "T_10": "✕", "T_11": "✕",
      "T_12": "✕", "T_13": "●", "T_14": "●", "T_15": "●",
      "T_16": "%", "T_17": "✕", "T_18": "✕", "T_19": "✕",
      "T_20": "✕", "T_21": "✕", "T_22": "✕", "T_23": "%"
    },
    "return_base64": false
  }' \
  --output grid_output.png
```

### Production Deployment

For production use with n8n:

1. **Deploy the HTTP server** to a cloud service (AWS, GCP, Azure, etc.)
2. **Use environment variables** for configuration
3. **Add authentication** if needed (API keys, OAuth, etc.)
4. **Set up reverse proxy** (nginx, Traefik) for SSL/TLS
5. **Configure CORS** if accessing from different domains

Example with environment variables:
```bash
docker run -d \
  -p 8000:8000 \
  -e PORT=8000 \
  -e HOST=0.0.0.0 \
  grid-image-generator-http
```

