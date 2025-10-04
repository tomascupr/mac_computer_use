#!/usr/bin/env python3
"""
Quick test to verify the MCP server can import and start properly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    try:
        from mcp.server.fastmcp import FastMCP
        print("✓ FastMCP imported successfully")
        
        from tools.computer import ComputerTool
        print("✓ ComputerTool imported successfully")
        
        from tools.base import ToolResult, ToolError
        print("✓ Base classes imported successfully")
        
        # Test ComputerTool initialization
        computer_tool = ComputerTool()
        print("✓ ComputerTool initialized successfully")
        print(f"✓ Screen dimensions: {computer_tool.width}x{computer_tool.height}")
        
        # Test MCP server initialization
        mcp = FastMCP("mac-computer-control")
        print("✓ MCP server initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing MCP server components...")
    success = test_imports()
    if success:
        print("\n✓ All tests passed! MCP server should work correctly.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Check the errors above.")
        sys.exit(1)