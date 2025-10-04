#!/usr/bin/env python3
"""
MCP Server for Mac Computer Use

This server wraps the deedy/mac_computer_use tools to provide computer control
functionality through the Model Context Protocol (MCP).
"""

import asyncio
import sys
import os
from typing import Any

# Add the current directory to Python path to import tools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from tools.computer import ComputerTool
from tools.base import ToolResult, ToolError

# Initialize the MCP server
mcp = FastMCP("mac-computer-control")

# Initialize the computer tool
computer_tool = ComputerTool()

@mcp.tool()
async def screenshot() -> str:
    """
    Take a screenshot of the current screen.
    
    Returns:
        str: Base64-encoded PNG image of the current screen
    """
    try:
        result = await computer_tool(action="screenshot")
        if result.error:
            return f"Error taking screenshot: {result.error}"
        if result.base64_image:
            return f"Screenshot captured successfully. Base64 image data: {result.base64_image[:100]}..."
        return "Screenshot captured but no image data returned"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


@mcp.tool()
async def click() -> str:
    """
    Click at the current cursor position.
    
    Returns:
        str: Result message indicating success or failure
    """
    try:
        result = await computer_tool(action="left_click")
        if result.error:
            return f"Error clicking: {result.error}"
        return "Successfully clicked at current cursor position"
    except Exception as e:
        return f"Error clicking: {str(e)}"


@mcp.tool()
async def click_at(x: int, y: int) -> str:
    """
    Move mouse to coordinates and then click.
    
    Args:
        x (int): X coordinate to click
        y (int): Y coordinate to click
        
    Returns:
        str: Result message indicating success or failure
    """
    try:
        # First move mouse to coordinates
        move_result = await computer_tool(action="mouse_move", coordinate=[x, y])
        if move_result.error:
            return f"Error moving to ({x}, {y}): {move_result.error}"
        
        # Then click at current position
        click_result = await computer_tool(action="left_click")
        if click_result.error:
            return f"Error clicking at ({x}, {y}): {click_result.error}"
        return f"Successfully clicked at coordinates ({x}, {y})"
    except Exception as e:
        return f"Error clicking: {str(e)}"


@mcp.tool()
async def type_text(text: str) -> str:
    """
    Type the specified text at the current cursor position.
    
    Args:
        text (str): The text to type
        
    Returns:
        str: Result message indicating success or failure
    """
    try:
        result = await computer_tool(action="type", text=text)
        if result.error:
            return f"Error typing text: {result.error}"
        return f"Successfully typed: {text}"
    except Exception as e:
        return f"Error typing text: {str(e)}"


@mcp.tool()
async def press_key(key: str) -> str:
    """
    Press a specific key or key combination.
    
    Args:
        key (str): Key to press (e.g., "Return", "ctrl+c", "cmd+v")
        
    Returns:
        str: Result message indicating success or failure
    """
    try:
        result = await computer_tool(action="key", text=key)
        if result.error:
            return f"Error pressing key '{key}': {result.error}"
        return f"Successfully pressed key: {key}"
    except Exception as e:
        return f"Error pressing key: {str(e)}"


@mcp.tool()
async def mouse_move(x: int, y: int) -> str:
    """
    Move the mouse cursor to the specified coordinates.
    
    Args:
        x (int): X coordinate to move to
        y (int): Y coordinate to move to
        
    Returns:
        str: Result message indicating success or failure
    """
    try:
        result = await computer_tool(action="mouse_move", coordinate=[x, y])
        if result.error:
            return f"Error moving mouse to ({x}, {y}): {result.error}"
        return f"Successfully moved mouse to coordinates ({x}, {y})"
    except Exception as e:
        return f"Error moving mouse: {str(e)}"


@mcp.tool()
async def right_click() -> str:
    """
    Right-click at the current cursor position.
    
    Returns:
        str: Result message indicating success or failure
    """
    try:
        result = await computer_tool(action="right_click")
        if result.error:
            return f"Error right-clicking: {result.error}"
        return "Successfully right-clicked at current cursor position"
    except Exception as e:
        return f"Error right-clicking: {str(e)}"


@mcp.tool()
async def right_click_at(x: int, y: int) -> str:
    """
    Move mouse to coordinates and then right-click.
    
    Args:
        x (int): X coordinate to right-click
        y (int): Y coordinate to right-click
        
    Returns:
        str: Result message indicating success or failure
    """
    try:
        # First move mouse to coordinates
        move_result = await computer_tool(action="mouse_move", coordinate=[x, y])
        if move_result.error:
            return f"Error moving to ({x}, {y}): {move_result.error}"
        
        # Then right-click at current position
        click_result = await computer_tool(action="right_click")
        if click_result.error:
            return f"Error right-clicking at ({x}, {y}): {click_result.error}"
        return f"Successfully right-clicked at coordinates ({x}, {y})"
    except Exception as e:
        return f"Error right-clicking: {str(e)}"


@mcp.tool()
async def double_click() -> str:
    """
    Double-click at the current cursor position.
    
    Returns:
        str: Result message indicating success or failure
    """
    try:
        result = await computer_tool(action="double_click")
        if result.error:
            return f"Error double-clicking: {result.error}"
        return "Successfully double-clicked at current cursor position"
    except Exception as e:
        return f"Error double-clicking: {str(e)}"


@mcp.tool()
async def double_click_at(x: int, y: int) -> str:
    """
    Move mouse to coordinates and then double-click.
    
    Args:
        x (int): X coordinate to double-click
        y (int): Y coordinate to double-click
        
    Returns:
        str: Result message indicating success or failure
    """
    try:
        # First move mouse to coordinates
        move_result = await computer_tool(action="mouse_move", coordinate=[x, y])
        if move_result.error:
            return f"Error moving to ({x}, {y}): {move_result.error}"
        
        # Then double-click at current position
        click_result = await computer_tool(action="double_click")
        if click_result.error:
            return f"Error double-clicking at ({x}, {y}): {click_result.error}"
        return f"Successfully double-clicked at coordinates ({x}, {y})"
    except Exception as e:
        return f"Error double-clicking: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run(transport="stdio")