# Issues Fixed

## Patient Chat Error: 'coroutine' object has no attribute 'get'

**Date Fixed:** Current date

### Issue Description

The patient-chat interface was encountering an error message: "Error processing message: 'coroutine' object has no attribute 'get'". This error occurred when users attempted to send messages through the chat interface.

### Root Cause

The root cause was identified in two places where asynchronous functions were being called without the required `await` keyword:

1. In `load_memory_to_graph` function in `src/ai_companion/graph/utils/helpers.py`: This function was calling `memory_service.load_memory_to_graph` without using the `await` keyword.

2. In the `MemoryService.load_memory_to_graph` method in `src/ai_companion/modules/memory/service.py`: This method was calling `graph.invoke` without using the `await` keyword.

In Python, when you call an asynchronous function without `await`, it returns a coroutine object instead of the actual result. When the code later tried to access attributes or methods on this coroutine (like using `.get()`), it failed with the error "'coroutine' object has no attribute 'get'".

### Fix Implemented

The solution was to add the `await` keyword before the calls to these asynchronous functions:

1. In helpers.py:
```python
# Before (broken):
result = memory_service.load_memory_to_graph(graph, config, session_id)

# After (fixed):
result = await memory_service.load_memory_to_graph(graph, config, session_id)
```

2. In memory_service.py:
```python
# Before (broken):
result = graph.invoke(state, config)

# After (fixed):
result = await graph.invoke(state, config)
```

### Additional Improvements

After the main fix, we also implemented several improvements to the test framework:

1. Fixed pytest-asyncio deprecation warnings:
   - Added proper `pytest.ini` configuration for asyncio settings
   - Updated the `event_loop` fixture in `conftest.py` to use the recommended approach

2. Fixed Qdrant Client deprecation warning:
   - Updated the `search_memories` method in `VectorStore` class to use `query_points` instead of the deprecated `search` method

3. Added comprehensive test tools:
   - Created a standalone verification script (`tests/verify_patient_chat_fix.py`)
   - Added a proper integration test suite (`tests/integration/test_patient_chat.py`)
   - Created a unified test runner script (`run_tests.py`) to run all verification tests

### Verification

After applying these fixes, the patient-chat interface now properly processes messages and provides responses from the AI assistant without the coroutine error. All tests pass successfully without errors.

#### Test Files

To verify the fix, we've created the following test files:

1. `tests/integration/test_patient_chat.py` - A comprehensive integration test suite that:
   - Tests the `load_memory_to_graph` function directly
   - Tests the `MemoryService.load_memory_to_graph` method
   - Tests the complete API endpoint flow with message handling
   - Tests multi-message conversations to ensure memory works correctly

2. `tests/verify_patient_chat_fix.py` - A standalone script that can be run directly to verify the fix:
   ```
   python tests/verify_patient_chat_fix.py
   ```
   This script specifically tests the two functions that were fixed, using mock objects to simulate the full environment.

3. `run_tests.py` - A unified test runner that runs both verification methods:
   ```
   python run_tests.py
   ```

To run the integration tests:
```
pytest -xvs tests/integration/test_patient_chat.py
```

### Lessons Learned

This issue highlights the importance of properly using `await` with all asynchronous function calls in Python. When working with asynchronous code:

1. Always use `await` when calling an asynchronous function (any function defined with `async def`)
2. Be careful when refactoring synchronous code to asynchronous, as missed `await` keywords can cause subtle bugs
3. Remember that calling an async function without `await` returns a coroutine object, not the function's result
4. When chaining async calls (calling one async function from another), each call in the chain needs its own `await`
5. Consider adding static type checking or linters that can detect missing `await` keywords
6. Properly configure testing tools like pytest-asyncio to avoid deprecation warnings

### Related Files

- `src/ai_companion/graph/utils/helpers.py` - Location of the first fix
- `src/ai_companion/modules/memory/service.py` - Location of the second fix
- `src/ai_companion/api/web_handler.py` - Module that uses these functions
- `src/ai_companion/modules/memory/long_term/vector_store.py` - Updated to fix deprecation warning
- `tests/conftest.py` - Updated to fix pytest-asyncio warnings
- `pytest.ini` - Added to configure pytest-asyncio properly 