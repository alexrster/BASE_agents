#!/usr/bin/env python3
"""
HTTP wrapper for MCP Server
Exposes the MCP server via HTTP/REST API for integration with n8n and other HTTP-based clients.
"""

import asyncio
import base64
import json
import tempfile
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
import uvicorn

from generate_grid_image import generate_image

app = FastAPI(
    title="Grid Image Generator MCP Server",
    description="HTTP API wrapper for the Grid Availability Image Generator MCP Server",
    version="1.0.0"
)


class GridData(BaseModel):
    """Grid availability data model."""
    T_Date: str = Field(..., description="Date in DD-MM-YYYY format (e.g., '20-11-2025')")
    T_00: Optional[str] = Field(None, description="State for hour 0: '●' (available), '✕' (unavailable), '%' (partial), '-' (unknown)")
    T_01: Optional[str] = None
    T_02: Optional[str] = None
    T_03: Optional[str] = None
    T_04: Optional[str] = None
    T_05: Optional[str] = None
    T_06: Optional[str] = None
    T_07: Optional[str] = None
    T_08: Optional[str] = None
    T_09: Optional[str] = None
    T_10: Optional[str] = None
    T_11: Optional[str] = None
    T_12: Optional[str] = None
    T_13: Optional[str] = None
    T_14: Optional[str] = None
    T_15: Optional[str] = None
    T_16: Optional[str] = None
    T_17: Optional[str] = None
    T_18: Optional[str] = None
    T_19: Optional[str] = None
    T_20: Optional[str] = None
    T_21: Optional[str] = None
    T_22: Optional[str] = None
    T_23: Optional[str] = None


class GenerateImageRequest(BaseModel):
    """Request model for image generation."""
    grid_data: GridData = Field(..., description="Grid availability data")
    return_base64: bool = Field(False, description="If true, return image as base64. If false, return as PNG binary.")


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
            "/tools/generate_grid_availability_image": "Generate grid availability image"
        }
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
                               "The image is 1024x250px and follows iOS design guidelines. "
                               "Input data should be a JSON object with T_Date (format: DD-MM-YYYY) and "
                               "T_00 through T_23 keys with values: '●' (available), '✕' (unavailable), "
                               "'%' (partial/transition), or '-' (unknown).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "grid_data": {
                            "type": "object",
                            "properties": {
                                "T_Date": {
                                    "type": "string",
                                    "description": "Date in DD-MM-YYYY format (e.g., '20-11-2025')"
                                },
                                "T_00": {"type": "string", "description": "State for hour 0"},
                                "T_01": {"type": "string", "description": "State for hour 1"},
                                "T_02": {"type": "string", "description": "State for hour 2"},
                                "T_03": {"type": "string", "description": "State for hour 3"},
                                "T_04": {"type": "string", "description": "State for hour 4"},
                                "T_05": {"type": "string", "description": "State for hour 5"},
                                "T_06": {"type": "string", "description": "State for hour 6"},
                                "T_07": {"type": "string", "description": "State for hour 7"},
                                "T_08": {"type": "string", "description": "State for hour 8"},
                                "T_09": {"type": "string", "description": "State for hour 9"},
                                "T_10": {"type": "string", "description": "State for hour 10"},
                                "T_11": {"type": "string", "description": "State for hour 11"},
                                "T_12": {"type": "string", "description": "State for hour 12"},
                                "T_13": {"type": "string", "description": "State for hour 13"},
                                "T_14": {"type": "string", "description": "State for hour 14"},
                                "T_15": {"type": "string", "description": "State for hour 15"},
                                "T_16": {"type": "string", "description": "State for hour 16"},
                                "T_17": {"type": "string", "description": "State for hour 17"},
                                "T_18": {"type": "string", "description": "State for hour 18"},
                                "T_19": {"type": "string", "description": "State for hour 19"},
                                "T_20": {"type": "string", "description": "State for hour 20"},
                                "T_21": {"type": "string", "description": "State for hour 21"},
                                "T_22": {"type": "string", "description": "State for hour 22"},
                                "T_23": {"type": "string", "description": "State for hour 23"},
                            },
                            "required": ["T_Date"]
                        },
                        "return_base64": {
                            "type": "boolean",
                            "description": "If true, return the image as a base64-encoded string.",
                            "default": False
                        }
                    },
                    "required": ["grid_data"]
                }
            }
        ]
    }


@app.post("/tools/generate_grid_availability_image")
async def generate_grid_availability_image(request: GenerateImageRequest):
    """Generate grid availability image."""
    try:
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
        
        # Generate the image
        generate_image(grid_data_dict, output_path)
        
        if request.return_base64:
            # Read image and convert to base64
            with open(output_path, "rb") as img_file:
                image_data = img_file.read()
                base64_data = base64.b64encode(image_data).decode("utf-8")
            
            return JSONResponse(content={
                "success": True,
                "message": "Grid availability image generated successfully",
                "image_size": "1024x250px",
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
async def generate_simple(request: GenerateImageRequest):
    """Simplified endpoint for n8n integration."""
    return await generate_grid_availability_image(request)


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)

