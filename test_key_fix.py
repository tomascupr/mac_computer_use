#!/usr/bin/env python3
"""Test script to verify the key combination fix works."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.computer import ComputerTool

async def test_key_combinations():
    """Test various key combinations with our fix."""
    
    computer = ComputerTool()
    
    test_cases = [
        "cmd+n",      # Should now work with cliclick
        "cmd+c",      # Should work with cliclick  
        "cmd+shift",  # Should work with keyboard library (no letters)
        "space",      # Should work with keyboard library
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case}")
        try:
            result = await computer(action="key", text=test_case)
            if result.error:
                print(f"  ❌ FAILED: {result.error}")
            else:
                print(f"  ✅ SUCCESS: {result.output}")
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_key_combinations())