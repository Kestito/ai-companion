# RAG System Bug Fix: Missing `cache_enabled` Attribute

## Issue Description

The RAG system was encountering an error during query execution:

```
Error in enhanced RAG chain query: 'LithuanianRAGChain' object has no attribute 'cache_enabled'
Error in RAG retry node query: 'LithuanianRAGChain' object has no attribute 'cache_enabled'  
```

The error occurred because:
1. The `query` method in `LithuanianRAGChain` tried to check `self.cache_enabled` to determine if caching should be used
2. However, this attribute was never initialized in the `__init__` method
3. Similarly, there was a reference to `self.query_count` in a conditional that wasn't initialized
4. The response creation methods returned dictionaries but the calling code expected tuples

## Fix Implementation

We made the following changes to fix the issues:

### 1. Added Missing Attributes to `__init__` Method

```python
# Added to __init__ method
self.cache_enabled = True  # Enable caching by default
self.query_count = 0  # Initialize query counter
```

### 2. Fixed Response Creation Methods

Updated the following methods to return tuples instead of dictionaries:
- `_create_no_docs_response`
- `_create_no_results_response`
- `_create_no_relevant_docs_response`

For example:
```python
def _create_no_docs_response(self, query_info: Dict[str, Any]) -> Tuple[str, List[Document]]:
    """Create Lithuanian response for no documents case."""
    response_text = f"Atsiprašau, bet nepavyko rasti jokių dokumentų, susijusių su jūsų klausimu. (Bandyta ieškoti Qdrant duomenų bazėje, kolekcija: {self.collection_name})"
    return (response_text, [])
```

### 3. Fixed Query Counter Increment

Moved the query counter increment to the beginning of the `query` method for reliable counting:

```python
# Increment query counter at the start of the method
self.query_count += 1
```

## Testing

We created a test script (`test_rag_fix.py`) to verify our fixes:

1. Test attribute access for `cache_enabled` and `query_count`
2. Run a query and check that `query_count` increments
3. Run the same query again to test caching behavior
4. Verify that `query_count` increments again

The test was successful, confirming that:
- The `cache_enabled` attribute is now properly initialized
- The `query_count` is correctly incremented
- Response methods return the expected tuple format

## Documentation Updates

We also updated the RAG system documentation to:
1. Add a section about the caching system in `project-docs/rag.md`
2. Document how to disable the cache
3. Explain the cache implementation, key generation, and LRU eviction

## Future Considerations

Some potential improvements for the future:
1. Add a configurable option to enable/disable caching in the constructor
2. Implement cache invalidation when documents are updated
3. Create a monitoring endpoint to view cache statistics
4. Configure cache time-to-live (TTL) settings 