#!/usr/bin/env python3
"""
MCP Server for Electricity Grid Availability Image Generator
Exposes the grid image generation functionality as an MCP tool.
"""

import asyncio
import base64
import json
import tempfile
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent
from generate_grid_image import generate_image

# Create the MCP server
server = Server("grid-image-generator")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="generate_grid_availability_image",
            description="Generate an image showing electricity grid availability for a given date. "
                       "The image is 1024x250px (horizontal) and follows iOS design guidelines. "
                       "Input data should be a JSON object with T_Date (format: DD-MM-YYYY) and "
                       "T_00 through T_23 keys with values: '●' (available), '✕' (unavailable), "
                       "'%' (partial/transition), or '-' (unknown).",
            inputSchema={
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
                    "output_path": {
                        "type": "string",
                        "description": "Optional output file path. If not provided, a temporary file will be used.",
                        "default": None
                    },
                    "return_base64": {
                        "type": "boolean",
                        "description": "If true, return the image as a base64-encoded string. If false, return the file path.",
                        "default": False
                    }
                },
                "required": ["grid_data"]
            }
        ),
        Tool(
            name="generate_grid_availability_image_vertical",
            description="Generate a vertical-oriented image showing electricity grid availability for a given date. "
                       "The image is 250x1024px (vertical) and follows iOS design guidelines. "
                       "Input data should be a JSON object with T_Date (format: DD-MM-YYYY) and "
                       "T_00 through T_23 keys with values: '●' (available), '✕' (unavailable), "
                       "'%' (partial/transition), or '-' (unknown).",
            inputSchema={
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
                    "output_path": {
                        "type": "string",
                        "description": "Optional output file path. If not provided, a temporary file will be used.",
                        "default": None
                    },
                    "return_base64": {
                        "type": "boolean",
                        "description": "If true, return the image as a base64-encoded string. If false, return the file path.",
                        "default": False
                    }
                },
                "required": ["grid_data"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
    """Handle tool calls."""
    if name == "generate_grid_availability_image":
        try:
            grid_data = arguments.get("grid_data", {})
            output_path = arguments.get("output_path")
            return_base64 = arguments.get("return_base64", False)
            
            # Validate required fields
            if "T_Date" not in grid_data:
                return [TextContent(
                    type="text",
                    text=f"Error: T_Date is required in grid_data"
                )]
            
            # Create temporary file if no output path provided
            if output_path is None:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                    output_path = tmp_file.name
            
            # Generate the image (horizontal)
            generate_image(grid_data, output_path, vertical=False)
            
            if return_base64:
                # Read image and convert to base64
                with open(output_path, "rb") as img_file:
                    image_data = img_file.read()
                    base64_data = base64.b64encode(image_data).decode("utf-8")
                
                return [
                    TextContent(
                        type="text",
                        text=f"Grid availability image generated successfully. Image size: 1024x250px"
                    ),
                    ImageContent(
                        type="image",
                        data=base64_data,
                        mimeType="image/png"
                    )
                ]
            else:
                return [TextContent(
                    type="text",
                    text=f"Grid availability image generated successfully at: {output_path}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error generating grid image: {str(e)}"
            )]
    elif name == "generate_grid_availability_image_vertical":
        try:
            grid_data = arguments.get("grid_data", {})
            output_path = arguments.get("output_path")
            return_base64 = arguments.get("return_base64", False)
            
            # Validate required fields
            if "T_Date" not in grid_data:
                return [TextContent(
                    type="text",
                    text=f"Error: T_Date is required in grid_data"
                )]
            
            # Create temporary file if no output path provided
            if output_path is None:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                    output_path = tmp_file.name
            
            # Generate the image (vertical)
            generate_image(grid_data, output_path, vertical=True)
            
            if return_base64:
                # Read image and convert to base64
                with open(output_path, "rb") as img_file:
                    image_data = img_file.read()
                    base64_data = base64.b64encode(image_data).decode("utf-8")
                
                return [
                    TextContent(
                        type="text",
                        text=f"Grid availability image generated successfully. Image size: 250x1024px"
                    ),
                    ImageContent(
                        type="image",
                        data=base64_data,
                        mimeType="image/png"
                    )
                ]
            else:
                return [TextContent(
                    type="text",
                    text=f"Grid availability image generated successfully at: {output_path}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error generating grid image: {str(e)}"
            )]
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

