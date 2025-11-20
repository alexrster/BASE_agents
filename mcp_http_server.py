#!/usr/bin/env python3
"""
HTTP wrapper for MCP Server
Exposes the MCP server via HTTP/REST API for integration with n8n and other HTTP-based clients.
"""

import asyncio
import base64
import json
import tempfile
from typing import Optional, AsyncGenerator
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from generate_grid_image import generate_image

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
            "/sse": "SSE endpoint for MCP protocol (for external tool registration)"
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
                        },
                        "vertical": {
                            "type": "boolean",
                            "description": "If true, generate vertical image (250x1024px). If false, generate horizontal image (1024x250px).",
                            "default": False
                        }
                    },
                    "required": ["grid_data"]
                }
            }
        ]
    }


@app.post("/tools/generate_grid_availability_image")
async def generate_grid_availability_image(
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
    return await generate_grid_availability_image(request, vertical=vertical)


async def handle_mcp_message(message: dict) -> dict:
    """Handle MCP protocol messages and return responses."""
    method = message.get("method")
    params = message.get("params", {})
    id = message.get("id")
    
    if method == "tools/list":
        # Return list of available tools
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "tools": [
                    {
                        "name": "generate_grid_availability_image",
                        "description": "Generate an image showing electricity grid availability for a given date. "
                                     "The image is 1024x250px (horizontal) or 250x1024px (vertical) and follows iOS design guidelines. "
                                     "Input data should be a JSON object with T_Date (format: DD-MM-YYYY) and "
                                     "T_00 through T_23 keys with values: '●' (available), '✕' (unavailable), "
                                     "'%' (partial/transition), or '-' (unknown).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "grid_data": {
                                    "type": "object",
                                    "description": "JSON object containing grid availability data. Must include T_Date (DD-MM-YYYY format) and T_00 through T_23 with state values.",
                                    "properties": {
                                        "T_Date": {
                                            "type": "string",
                                            "description": "Date in DD-MM-YYYY format (e.g., '20-11-2025')"
                                        },
                                        "T_00": {"type": "string", "description": "State for hour 0: '●' (available), '✕' (unavailable), '%' (partial), '-' (unknown)"},
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
                                "vertical": {
                                    "type": "boolean",
                                    "description": "If true, generate vertical image (250x1024px). If false, generate horizontal image (1024x250px).",
                                    "default": False
                                },
                                "return_base64": {
                                    "type": "boolean",
                                    "description": "If true, return the image as a base64-encoded string. If false, return the file path.",
                                    "default": False
                                }
                            },
                            "required": ["grid_data"]
                        }
                    },
                    {
                        "name": "generate_grid_availability_image_vertical",
                        "description": "Generate a vertical-oriented image showing electricity grid availability for a given date. "
                                     "The image is 250x1024px (vertical) and follows iOS design guidelines. "
                                     "Input data should be a JSON object with T_Date (format: DD-MM-YYYY) and "
                                     "T_00 through T_23 keys with values: '●' (available), '✕' (unavailable), "
                                     "'%' (partial/transition), or '-' (unknown).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "grid_data": {
                                    "type": "object",
                                    "description": "JSON object containing grid availability data. Must include T_Date (DD-MM-YYYY format) and T_00 through T_23 with state values.",
                                    "properties": {
                                        "T_Date": {
                                            "type": "string",
                                            "description": "Date in DD-MM-YYYY format (e.g., '20-11-2025')"
                                        },
                                        "T_00": {"type": "string", "description": "State for hour 0: '●' (available), '✕' (unavailable), '%' (partial), '-' (unknown)"},
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
                                    "description": "If true, return the image as a base64-encoded string. If false, return the file path.",
                                    "default": False
                                }
                            },
                            "required": ["grid_data"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        # Handle tool call
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            grid_data = arguments.get("grid_data", {})
            vertical = arguments.get("vertical", False)
            return_base64 = arguments.get("return_base64", False)
            
            # Handle vertical tool
            if tool_name == "generate_grid_availability_image_vertical":
                vertical = True
            
            # Validate required fields
            if "T_Date" not in grid_data:
                return {
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {
                        "code": -32602,
                        "message": "T_Date is required in grid_data"
                    }
                }
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Generate the image
            generate_image(grid_data, output_path, vertical=vertical)
            
            # Determine image size
            image_size = "250x1024px" if vertical else "1024x250px"
            
            if return_base64:
                # Read image and convert to base64
                with open(output_path, "rb") as img_file:
                    image_data = img_file.read()
                    base64_data = base64.b64encode(image_data).decode("utf-8")
                
                return {
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Grid availability image generated successfully. Image size: {image_size}"
                            },
                            {
                                "type": "image",
                                "data": base64_data,
                                "mimeType": "image/png"
                            }
                        ]
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Grid availability image generated successfully at: {output_path}. Image size: {image_size}"
                            }
                        ]
                    }
                }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": id,
                "error": {
                    "code": -32603,
                    "message": f"Error generating grid image: {str(e)}"
                }
            }
    
    elif method == "initialize":
        # Handle initialization
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "grid-image-generator",
                    "version": "1.0.0"
                }
            }
        }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


async def sse_stream(request: Request) -> AsyncGenerator[str, None]:
    """SSE stream handler for MCP protocol."""
    try:
        # Send initial connection message
        yield "data: " + json.dumps({"type": "connection", "status": "connected"}) + "\n\n"
        
        # For POST requests, read the body
        if request.method == "POST":
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON-RPC message
                    try:
                        message = json.loads(body.decode("utf-8"))
                        response = await handle_mcp_message(message)
                        yield "data: " + json.dumps(response) + "\n\n"
                    except json.JSONDecodeError:
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32700,
                                "message": "Parse error"
                            }
                        }
                        yield "data: " + json.dumps(error_response) + "\n\n"
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Error processing request: {str(e)}"
                    }
                }
                yield "data: " + json.dumps(error_response) + "\n\n"
        
        # For GET requests or streaming, handle incoming messages
        async for line in request.stream():
            try:
                # Parse incoming message
                if line.startswith(b"data: "):
                    message_str = line[6:].decode("utf-8").strip()
                    if message_str:
                        message = json.loads(message_str)
                        
                        # Handle MCP message
                        response = await handle_mcp_message(message)
                        
                        # Send response as SSE event
                        yield "data: " + json.dumps(response) + "\n\n"
                
                # Handle ping/pong for keepalive
                elif line.strip() == b"":
                    yield ": keepalive\n\n"
            
            except json.JSONDecodeError:
                # Invalid JSON, send error
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                yield "data: " + json.dumps(error_response) + "\n\n"
            
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                yield "data: " + json.dumps(error_response) + "\n\n"
    
    except Exception as e:
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Stream error: {str(e)}"
            }
        }
        yield "data: " + json.dumps(error_response) + "\n\n"


@app.get("/sse")
@app.post("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP protocol.
    
    This endpoint allows external tools to connect via Server-Sent Events (SSE)
    and communicate using the MCP protocol.
    
    Usage:
        Connect to: GET /sse or POST /sse
        For POST: Send JSON-RPC message in request body
        For GET: Stream messages as: data: {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        Receive responses as SSE events
    
    Example POST request:
        POST /sse
        Content-Type: application/json
        Body: {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
    """
    return StreamingResponse(
        sse_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


@app.options("/sse")
async def sse_options():
    """Handle CORS preflight requests for SSE endpoint."""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)

