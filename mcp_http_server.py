#!/usr/bin/env python3
"""
HTTP wrapper for MCP Server using FastMCP
Exposes the MCP server via HTTP/REST API for integration with n8n and other HTTP-based clients.
FastMCP handles HTTP/SSE transport automatically via mcp.run(transport="http").
"""

import base64
import tempfile
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from mcp_server import GridData
from generate_grid_image import generate_image

# Create FastAPI app for REST endpoints
app = FastAPI(
    title="Grid Image Generator MCP Server",
    description="HTTP API wrapper for the Grid Availability Image Generator MCP Server",
    version="1.0.0"
)

# Add CORS middleware for SSE support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateImageRequest(BaseModel):
    """Request model for image generation."""
    grid_data: GridData = Field(..., description="Grid availability data")
    return_base64: bool = Field(False, description="If true, return image as base64. If false, return as PNG binary.")
    vertical: bool = Field(False, description="If true, generate vertical image (250x1024px). If false, generate horizontal image (1024x250px).")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Grid Image Generator MCP Server",
        "version": "1.0.0",
        "description": "HTTP API wrapper for generating electricity grid availability images",
        "endpoints": {
            "/health": "Health check endpoint",
            "/tools": "List available tools",
            "/tools/generate_grid_availability_image": "Generate grid availability image",
            "/generate": "Simplified endpoint for n8n integration"
        },
        "note": "For MCP protocol endpoints, run mcp_server.py with transport='http' or use FastMCP's built-in HTTP transport"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "grid-image-generator"}


@app.get("/tools")
async def list_tools():
    """List available tools (MCP-compatible)."""
    return {
        "tools": [
            {
                "name": "generate_grid_availability_image",
                "description": "Generate an image showing electricity grid availability for a given date. "
                               "The image is 1024x250px (horizontal) or 250x1024px (vertical) and follows iOS design guidelines.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "grid_data": {"type": "object"},
                        "vertical": {"type": "boolean", "default": False},
                        "return_base64": {"type": "boolean", "default": False}
                    },
                    "required": ["grid_data"]
                }
            },
            {
                "name": "generate_grid_availability_image_vertical",
                "description": "Generate a vertical-oriented image (250x1024px) showing electricity grid availability.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "grid_data": {"type": "object"},
                        "return_base64": {"type": "boolean", "default": False}
                    },
                    "required": ["grid_data"]
                }
            }
        ]
    }


@app.post("/tools/generate_grid_availability_image")
async def generate_grid_availability_image_rest(
    request: GenerateImageRequest,
    vertical: bool = Query(False, description="If true, generate vertical image (250x1024px)")
):
    """Generate grid availability image.
    
    Supports vertical parameter both in request body and as query parameter.
    Query parameter takes precedence if both are provided.
    """
    try:
        # Override vertical from query parameter if provided
        is_vertical = vertical or request.vertical
        
        # Convert Pydantic model to dict (compatible with both v1 and v2)
        try:
            # Pydantic v2
            grid_data_dict = request.grid_data.model_dump(exclude_none=True)
        except AttributeError:
            # Pydantic v1 fallback
            grid_data_dict = request.grid_data.dict(exclude_none=True)
        
        # Validate required fields
        if "T_Date" not in grid_data_dict:
            raise HTTPException(status_code=400, detail="T_Date is required in grid_data")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            output_path = tmp_file.name
        
        # Generate the image (with vertical parameter)
        generate_image(grid_data_dict, output_path, vertical=is_vertical)
        
        # Determine image size string
        image_size = "250x1024px" if is_vertical else "1024x250px"
        
        if request.return_base64:
            # Read image and convert to base64
            with open(output_path, "rb") as img_file:
                image_data = img_file.read()
                base64_data = base64.b64encode(image_data).decode("utf-8")
            
            return JSONResponse(content={
                "success": True,
                "message": "Grid availability image generated successfully",
                "image_size": image_size,
                "image_base64": base64_data,
                "mime_type": "image/png"
            })
        else:
            # Return image as binary
            with open(output_path, "rb") as img_file:
                image_data = img_file.read()
            
            return Response(
                content=image_data,
                media_type="image/png",
                headers={
                    "Content-Disposition": f"attachment; filename=grid_availability_{grid_data_dict['T_Date'].replace('-', '_')}.png"
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating grid image: {str(e)}")


@app.post("/generate")
async def generate_simple(
    request: GenerateImageRequest,
    vertical: bool = Query(False, description="If true, generate vertical image (250x1024px)")
):
    """Simplified endpoint for n8n integration.
    
    Supports vertical parameter as query parameter for easier integration.
    Example: POST /generate?vertical=true
    """
    return await generate_grid_availability_image_rest(request, vertical=vertical)


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Run FastAPI app with REST endpoints
    # For MCP protocol endpoints, run: python mcp_server.py with transport="http"
    # or use FastMCP's built-in HTTP transport: mcp.run(transport="http", host=host, port=port)
    uvicorn.run(app, host=host, port=port)
