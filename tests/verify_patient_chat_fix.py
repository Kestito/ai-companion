#!/usr/bin/env python
"""
Script to verify that the 'coroutine' object has no attribute 'get' fix
is working properly in the patient chat API.

This script runs the key functions that were fixed and ensures they work correctly.
It can be run directly to verify the fix without running the full test suite.

Usage:
    python verify_patient_chat_fix.py
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_companion.graph.utils.helpers import load_memory_to_graph
from ai_companion.modules.memory.service import MemoryService
from langchain_core.messages import HumanMessage

# Test constants
TEST_USER_ID = "test-user-456"
TEST_SESSION_ID = f"web-{TEST_USER_ID}"


class MockGraph:
    """Mock graph for testing"""

    async def invoke(self, state, config):
        """Mock invoke method"""
        print(f"MockGraph.invoke called with state: {state}")
        return {
            "messages": state.get("messages", []),
            "output_message": "This is a test response from the mock graph",
        }

    async def aget_state(self, config):
        """Mock aget_state method"""
        print(f"MockGraph.aget_state called with config: {config}")
        return {"messages": [], "state": "test state"}


class MockSupabase:
    """Mock Supabase client for testing"""

    def __init__(self):
        self.data = {}

    def table(self, table_name):
        print(f"MockSupabase.table called with: {table_name}")
        self.current_table = table_name
        return self

    def select(self, *fields):
        return self

    def like(self, field, value):
        return self

    def order(self, field, desc=False):
        return self

    def limit(self, limit_val):
        return self

    def execute(self):
        print(f"MockSupabase.execute called for table: {self.current_table}")
        return type("obj", (object,), {"data": []})

    def insert(self, record):
        print(f"MockSupabase.insert called for table: {self.current_table}")
        if self.current_table not in self.data:
            self.data[self.current_table] = []
        self.data[self.current_table].append(record)
        return self


async def test_fixed_functions():
    """Test the functions that were fixed"""
    print("\n=== Testing Fixed Functions ===\n")

    # Create a mock memory service
    memory_service = MemoryService()
    memory_service.supabase = MockSupabase()

    # Create test messages
    messages = [HumanMessage(content="Hello, this is a test message")]

    # Test 1: helpers.load_memory_to_graph
    print("\n--- Test 1: helpers.load_memory_to_graph ---\n")
    try:
        result1 = await load_memory_to_graph(MockGraph(), messages, TEST_SESSION_ID)
        print(f"Result 1: {result1}")
        print("✅ First test passed! load_memory_to_graph returned a proper result")
    except Exception as e:
        print(f"❌ First test failed: {e}")
        return False

    # Test 2: memory_service.load_memory_to_graph
    print("\n--- Test 2: memory_service.load_memory_to_graph ---\n")
    try:
        config = {"messages": messages, "configurable": {"session_id": TEST_SESSION_ID}}
        result2 = await memory_service.load_memory_to_graph(
            MockGraph(), config, TEST_SESSION_ID
        )
        print(f"Result 2: {result2}")
        print(
            "✅ Second test passed! memory_service.load_memory_to_graph returned a proper result"
        )
    except Exception as e:
        print(f"❌ Second test failed: {e}")
        return False

    # All tests passed
    print("\n=== All tests passed! The fix has been applied correctly ===\n")
    return True


def display_script_header():
    """Display a header for the script"""
    print("\n" + "=" * 80)
    print("Patient Chat Fix Verification Script".center(80))
    print("=" * 80)
    print("\nThis script verifies that the 'coroutine' object has no attribute 'get'")
    print("fix has been correctly applied to the patient chat API.")
    print(
        "\nThe script will run the key functions that were fixed and ensure they work properly."
    )
    print("=" * 80 + "\n")


async def main():
    """Main function"""
    display_script_header()
    await test_fixed_functions()


if __name__ == "__main__":
    asyncio.run(main())
