-- First, drop existing functions to ensure clean installation
DROP FUNCTION IF EXISTS public.search_documents(TEXT, INT, BOOLEAN, FLOAT);
DROP FUNCTION IF EXISTS public.search_documents(TEXT, INT);
DROP FUNCTION IF EXISTS public.search_documents(TEXT);
DROP FUNCTION IF EXISTS public.test_search_function(TEXT);
DROP FUNCTION IF EXISTS public.test_search_function();

-- Create text search indexes for improved search performance
CREATE INDEX IF NOT EXISTS idx_document_chunks_content ON public.document_chunks 
USING gin (to_tsvector('simple', chunk_content));

CREATE INDEX IF NOT EXISTS idx_document_chunks_title ON public.document_chunks 
USING gin (to_tsvector('simple', title));

-- First, create the necessary indexes if they don't exist
DO $$
BEGIN
    -- Check if the text search index exists on chunk_content
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE indexname = 'idx_document_chunks_chunk_content_search'
    ) THEN
        -- Create a GIN index on the document_chunks table for faster text search
        CREATE INDEX idx_document_chunks_chunk_content_search
        ON public.document_chunks
        USING gin(to_tsvector('simple', chunk_content));
        
        RAISE NOTICE 'Created text search index on document_chunks.chunk_content';
    END IF;
    
    -- Check if the index on document_id exists
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE indexname = 'idx_document_chunks_document_id'
    ) THEN
        -- Create index for faster joins between documents and chunks
        CREATE INDEX idx_document_chunks_document_id
        ON public.document_chunks(document_id);
        
        RAISE NOTICE 'Created index on document_chunks.document_id';
    END IF;
    
    -- Additional index for title search
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE indexname = 'idx_document_chunks_title_search'
    ) THEN
        -- Create a GIN index on the document_chunks table for faster text search on titles
        CREATE INDEX idx_document_chunks_title_search
        ON public.document_chunks
        USING gin(to_tsvector('simple', title));
        
        RAISE NOTICE 'Created text search index on document_chunks.title';
    END IF;
END
$$;

-- Create the main search function without overloads
CREATE OR REPLACE FUNCTION public.search_documents(
    query_text TEXT,
    limit_val INTEGER DEFAULT 10,
    include_title_search BOOLEAN DEFAULT TRUE,
    min_rank FLOAT DEFAULT 0.01
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
DECLARE
    normalized_query TEXT;
    search_query tsquery;
BEGIN
    -- Input validation
    IF query_text IS NULL OR trim(query_text) = '' THEN
        RAISE EXCEPTION 'Query text cannot be empty';
    END IF;
    
    IF limit_val <= 0 THEN
        limit_val := 10; -- Default to 10 if invalid
    END IF;
    
    -- Normalize query text to improve search quality
    normalized_query := trim(query_text);
    
    -- Convert to tsquery with proper error handling
    BEGIN
        search_query := plainto_tsquery('simple', normalized_query);
        
        -- If conversion fails or produces empty query, use simpler approach
        IF search_query::text = '' THEN
            -- Fall back to using the words directly
            search_query := to_tsquery('simple', 
                replace(regexp_replace(normalized_query, '[^\w\s]', ' ', 'g'), ' ', ' & ')
            );
        END IF;
    EXCEPTION WHEN OTHERS THEN
        -- Log error and use a simplified fallback approach
        RAISE NOTICE 'Error converting to tsquery: %, using fallback', SQLERRM;
        -- Create simple query with words connected by AND
        search_query := to_tsquery('simple', 
            replace(regexp_replace(normalized_query, '[^\w\s]', ' ', 'g'), ' ', ' & ')
        );
    END;
    
    -- Execute search with both content and title if requested
    IF include_title_search THEN
        RETURN QUERY
        SELECT 
            dc.id,
            dc.document_id,
            dc.title,
            dc.chunk_content,
            GREATEST(
                ts_rank(to_tsvector('simple', dc.chunk_content), search_query),
                ts_rank(to_tsvector('simple', dc.title), search_query) * 1.5  -- Boost title matches
            ) as rank,
            d.url,
            d.source_type
        FROM 
            public.document_chunks dc
        JOIN 
            public.documents d ON dc.document_id = d.id
        WHERE 
            to_tsvector('simple', dc.chunk_content) @@ search_query
            OR to_tsvector('simple', dc.title) @@ search_query
        ORDER BY 
            rank DESC
        LIMIT 
            limit_val;
    ELSE
        -- Search only in content for cases where title search is not needed
        RETURN QUERY
        SELECT 
            dc.id,
            dc.document_id,
            dc.title,
            dc.chunk_content,
            ts_rank(to_tsvector('simple', dc.chunk_content), search_query) as rank,
            d.url,
            d.source_type
        FROM 
            public.document_chunks dc
        JOIN 
            public.documents d ON dc.document_id = d.id
        WHERE 
            to_tsvector('simple', dc.chunk_content) @@ search_query
            AND ts_rank(to_tsvector('simple', dc.chunk_content), search_query) >= min_rank
        ORDER BY 
            rank DESC
        LIMIT 
            limit_val;
    END IF;
    
EXCEPTION WHEN OTHERS THEN
    -- Log error
    RAISE NOTICE 'Error in search_documents: %', SQLERRM;
    -- Return empty result set
    RETURN;
END;
$$; 

-- Grant execute permissions to all users for simplicity
GRANT EXECUTE ON FUNCTION public.search_documents(TEXT, INTEGER, BOOLEAN, FLOAT) TO public;

-- Create a corrected test function
CREATE OR REPLACE FUNCTION public.test_search_function(
    test_query TEXT DEFAULT 'POLA'
)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result_count INTEGER;
    execution_time FLOAT;
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    status TEXT;
BEGIN
    -- Record start time
    start_time := clock_timestamp();
    
    -- Execute the search and count results
    SELECT COUNT(*) INTO result_count
    FROM public.search_documents(test_query, 5);
    
    -- Record end time
    end_time := clock_timestamp();
    execution_time := extract(epoch from (end_time - start_time));
    
    -- Generate status message
    IF result_count > 0 THEN
        status := 'SUCCESS';
    ELSE
        status := 'WARNING: No results found';
    END IF;
    
    -- Use ROUND() for precise decimal places instead of format specifier
    RETURN format('Test result: %s - Found %s results for query "%s" in %s seconds',
                  status, result_count, test_query, ROUND(execution_time::numeric, 3));
EXCEPTION WHEN OTHERS THEN
    RETURN format('ERROR testing search_documents: %s', SQLERRM);
END;
$$;

-- Grant execute on test function to all users
GRANT EXECUTE ON FUNCTION public.test_search_function(TEXT) TO public; 