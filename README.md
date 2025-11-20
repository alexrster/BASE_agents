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

