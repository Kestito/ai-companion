def get_cached_response(query):
    # Potential cache stampede risk
    if not cache.exists(query):  # No lock mechanism
        return generate_response(query)
    return cache.get(query) 