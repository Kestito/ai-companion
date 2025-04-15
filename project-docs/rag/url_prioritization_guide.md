# URL Prioritization in RAG Guide

This guide explains how to use the URL prioritization feature in the RAG system to ensure specific content sources are boosted in search results.

## Overview

Sometimes you want your RAG system to prioritize content from specific sources when responding to certain queries. For example, you might want to ensure that when users ask about lung cancer (plaučių vėžys), the system primarily draws information from your trusted medical resource at `https://priesvezi.lt/zinynas/onkologines-ligos/plauciu-vezys/`.

The URL prioritization feature allows you to:
- Boost the ranking of documents from specific URLs
- Ensure trusted sources are prioritized for specific topics
- Overcome the "finding the right URL" problem in RAG systems

## How it Works

When you use URL prioritization:
1. The system performs its normal parallel search (semantic + keyword)
2. During the ranking phase, any documents from your prioritized URLs receive a 50% boost to their relevance score
3. This makes it much more likely that content from your specified URLs will appear at the top of the results

## Basic Usage

### Using the Convenience Function

The simplest way to use URL prioritization is with the `query_with_url_priority` function:

```python
from src.ai_companion.modules.rag.core import query_with_url_priority

# Query with a prioritized URL
response, docs = await query_with_url_priority(
    query="Kas yra plaučių vėžys?",
    priority_url="https://priesvezi.lt/zinynas/onkologines-ligos/plauciu-vezys/",
    min_confidence=0.7  # Optional: set minimum confidence threshold
)

# Print the response
print(response)

# Check if priority documents were used
for doc in docs:
    url = doc.metadata.get("url", "")
    if "priesvezi.lt/zinynas/onkologines-ligos/plauciu-vezys" in url:
        print(f"Used priority document: {url}")
```

### Using the RAG Chain Directly

If you need more control, you can use the RAG chain directly:

```python
from src.ai_companion.modules.rag.core import get_rag_chain

# Get the RAG chain
rag_chain = get_rag_chain()

# Execute query with prioritized URLs
response, docs = await rag_chain.query(
    query="Kas yra plaučių vėžys?",
    min_confidence=0.7,
    prioritized_urls=["https://priesvezi.lt/zinynas/onkologines-ligos/plauciu-vezys/"]
)
```

## Advanced Usage

### Multiple Priority URLs

You can prioritize multiple URLs at once:

```python
response, docs = await rag_chain.query(
    query="Kas yra plaučių vėžys?",
    prioritized_urls=[
        "https://priesvezi.lt/zinynas/onkologines-ligos/plauciu-vezys/",
        "https://another-trusted-source.lt/plauciu-vezys/"
    ]
)
```

### Combining with Other Filters

URL prioritization can be combined with other filter conditions:

```python
response, docs = await rag_chain.query(
    query="Kas yra plaučių vėžys?",
    prioritized_urls=["https://priesvezi.lt/zinynas/onkologines-ligos/plauciu-vezys/"],
    filter_conditions={
        "language": "lt",
        "source_type": "medical"
    }
)
```

## Example Application

A complete example is available in `examples/priority_url_rag.py`. It demonstrates:
- Setting up URL prioritization
- Processing multiple queries
- Checking which documents came from priority URLs
- Comparing scores between priority and non-priority documents

## Troubleshooting

### URL Not Being Prioritized

If your URL isn't being prioritized:

1. Check URL format - make sure the URL in your database exactly matches what you're specifying
2. Case sensitivity - the matching is case-insensitive, but ensure otherwise correct formatting
3. Presence in database - confirm the URL exists in your database
4. Logging - check logs for "Boosting document from prioritized URL" messages

### Monitoring Priority Usage

You can monitor how often priority URLs are being used:

```python
# Count prioritized documents
prioritized_count = 0
for doc in docs:
    if doc.metadata.get("url") and priority_url.lower() in doc.metadata.get("url", "").lower():
        prioritized_count += 1
        
print(f"Query returned {len(docs)} documents, {prioritized_count} from priority URL")
```

## Customizing Boost Factor

The default boost factor is 1.5 (50% boost). If you need to adjust this:

1. Edit `src/ai_companion/modules/rag/core/vector_store.py`
2. Find the line `url_boost = 1.5` in the prioritized URL section
3. Change to your desired boost factor (e.g., 2.0 for a 100% boost)

## Conclusion

URL prioritization is a powerful feature for ensuring specific trusted content sources are properly utilized in your RAG system. By boosting the relevance of documents from specific URLs, you can overcome common challenges with URL finding and ensure your system provides information from your preferred sources. 