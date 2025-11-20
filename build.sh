#!/bin/bash
# Build script for Docker image

set -e

echo "Building grid-image-generator Docker image..."
docker build -t grid-image-generator .

echo "Build complete! You can now run:"
echo "  docker run -i --rm grid-image-generator"
echo "  or"
echo "  docker-compose up -d"

