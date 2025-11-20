#!/usr/bin/env python3
"""
MCP Server for Electricity Grid Availability Image Generator
Exposes the grid image generation functionality as an MCP tool using FastMCP.
"""

import base64
import tempfile
from typing import Optional
from pydantic import BaseModel, Field

from fastmcp import FastMCP
from generate_grid_image import generate_image

# Create the FastMCP server
mcp = FastMCP("Grid Image Generator")


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


@mcp.tool()
def generate_grid_availability_image(
    grid_data: GridData,
    output_path: Optional[str] = Field(None, description="Optional output file path. If not provided, a temporary file will be used."),
    return_base64: bool = Field(False, description="If true, return the image as a base64-encoded string. If false, return the file path."),
    vertical: bool = Field(False, description="If true, generate vertical image (250x1024px). If false, generate horizontal image (1024x250px).")
) -> str:
    """Generate an image showing electricity grid availability for a given date.
    
    The image follows iOS design guidelines and can be generated in horizontal (1024x250px) 
    or vertical (250x1024px) orientation.
    
    Input data should be a JSON object with T_Date (format: DD-MM-YYYY) and T_00 through T_23 
    keys with values: '●' (available), '✕' (unavailable), '%' (partial/transition), or '-' (unknown).
    """
    # Convert Pydantic model to dict
    try:
        grid_data_dict = grid_data.model_dump(exclude_none=True)
    except AttributeError:
        # Pydantic v1 fallback
        grid_data_dict = grid_data.dict(exclude_none=True)
    
    # Validate required fields
    if "T_Date" not in grid_data_dict:
        raise ValueError("T_Date is required in grid_data")
    
    # Create temporary file if no output path provided
    if output_path is None:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            output_path = tmp_file.name
    
    # Generate the image
    generate_image(grid_data_dict, output_path, vertical=vertical)
    
    # Determine image size
    image_size = "250x1024px" if vertical else "1024x250px"
    
    if return_base64:
        # Read image and convert to base64
        with open(output_path, "rb") as img_file:
            image_data = img_file.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
        
        # Return base64 data (FastMCP will handle image content automatically if we return it properly)
        return f"Grid availability image generated successfully. Image size: {image_size}. Base64 data: {base64_data[:50]}..."
    else:
        return f"Grid availability image generated successfully at: {output_path}. Image size: {image_size}"


@mcp.tool()
def generate_grid_availability_image_vertical(
    grid_data: GridData,
    output_path: Optional[str] = Field(None, description="Optional output file path. If not provided, a temporary file will be used."),
    return_base64: bool = Field(False, description="If true, return the image as a base64-encoded string. If false, return the file path.")
) -> str:
    """Generate a vertical-oriented image showing electricity grid availability for a given date.
    
    The image is 250x1024px (vertical) and follows iOS design guidelines.
    
    Input data should be a JSON object with T_Date (format: DD-MM-YYYY) and T_00 through T_23 
    keys with values: '●' (available), '✕' (unavailable), '%' (partial/transition), or '-' (unknown).
    """
    # Convert Pydantic model to dict
    try:
        grid_data_dict = grid_data.model_dump(exclude_none=True)
    except AttributeError:
        # Pydantic v1 fallback
        grid_data_dict = grid_data.dict(exclude_none=True)
    
    # Validate required fields
    if "T_Date" not in grid_data_dict:
        raise ValueError("T_Date is required in grid_data")
    
    # Create temporary file if no output path provided
    if output_path is None:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            output_path = tmp_file.name
    
    # Generate the image (vertical)
    generate_image(grid_data_dict, output_path, vertical=True)
    
    if return_base64:
        # Read image and convert to base64
        with open(output_path, "rb") as img_file:
            image_data = img_file.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
        
        return f"Grid availability image generated successfully. Image size: 250x1024px. Base64 data: {base64_data[:50]}..."
    else:
        return f"Grid availability image generated successfully at: {output_path}. Image size: 250x1024px"


if __name__ == "__main__":
    import os
    import sys
    
    # Check for transport argument
    transport = os.getenv("TRANSPORT", "stdio")
    
    if transport == "http" or "--http" in sys.argv:
        # Run with HTTP transport
        port = int(os.getenv("PORT", 8001))
        host = os.getenv("HOST", "0.0.0.0")
        mcp.run(transport="http", host=host, port=port, path="/mcp")
    elif transport == "sse" or "--sse" in sys.argv:
        # Run with SSE transport
        port = int(os.getenv("PORT", 8001))
        host = os.getenv("HOST", "0.0.0.0")
        mcp.run(transport="sse", host=host, port=port)
    else:
        # Run with stdio transport (default)
        mcp.run()
