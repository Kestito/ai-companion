-- Create the RPC function for text search in document chunks in the public schema
CREATE OR REPLACE FUNCTION public.search_documents(
    query_text TEXT,
    limit_val INT DEFAULT 10
) 
RETURNS TABLE (
    id UUID,
    document_id UUID,
    title TEXT,
    chunk_content TEXT,
    rank REAL,
    url TEXT,
    source_type TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id,
        dc.document_id,
        dc.title,
        dc.chunk_content,
        ts_rank(
            to_tsvector('simple', dc.chunk_content), 
            plainto_tsquery('simple', query_text)
        ) as rank,
        d.url,
        d.source_type
    FROM 
        information_search.document_chunks dc
    JOIN 
        information_search.documents d ON dc.document_id = d.id
    WHERE 
        to_tsvector('simple', dc.chunk_content) @@ plainto_tsquery('simple', query_text)
    ORDER BY 
        rank DESC
    LIMIT 
        limit_val;
END;
$$; 