-- ================================================================
--  SUPABASE SETUP SCRIPT  —  Run this ONCE in Supabase SQL Editor
--  Dashboard → SQL Editor → New Query → paste all → Run
-- ================================================================

-- 1. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Policy chunks table
CREATE TABLE IF NOT EXISTS policy_chunks (
    id              TEXT PRIMARY KEY,
    content         TEXT        NOT NULL,
    embedding       vector(384),                   -- all-MiniLM-L6-v2 = 384 dims
    department      TEXT        NOT NULL,
    policy_type     TEXT        NOT NULL,
    source          TEXT        NOT NULL,
    file_type       TEXT        NOT NULL DEFAULT 'txt',
    chunk_index     INTEGER     NOT NULL DEFAULT 0,
    file_hash       TEXT        NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ          DEFAULT NOW()
);

-- 3. File tracking (skip unchanged files on re-ingest)
CREATE TABLE IF NOT EXISTS ingested_files (
    id          TEXT        PRIMARY KEY,
    file_hash   TEXT        NOT NULL,
    chunk_count INTEGER     NOT NULL DEFAULT 0,
    ingested_at TIMESTAMPTZ          DEFAULT NOW()
);

-- 4. Vector index (cosine similarity)
CREATE INDEX IF NOT EXISTS policy_chunks_embedding_idx
    ON policy_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- 5. Metadata filter indexes
CREATE INDEX IF NOT EXISTS idx_chunks_dept    ON policy_chunks (department);
CREATE INDEX IF NOT EXISTS idx_chunks_ptype   ON policy_chunks (policy_type);
CREATE INDEX IF NOT EXISTS idx_chunks_source  ON policy_chunks (source);

-- 6. Disable Row Level Security (service role key bypasses anyway, but be explicit)
ALTER TABLE policy_chunks  DISABLE ROW LEVEL SECURITY;
ALTER TABLE ingested_files DISABLE ROW LEVEL SECURITY;

-- ================================================================
--  7. RPC FUNCTION — called by backend for vector similarity search
--     This is the heart of RAG: finds top-K most relevant policy chunks
-- ================================================================
CREATE OR REPLACE FUNCTION match_policy_chunks(
    query_embedding  vector(384),
    match_count      int     DEFAULT 6,
    filter_dept      text    DEFAULT '',
    filter_ptype     text    DEFAULT ''
)
RETURNS TABLE (
    id           text,
    content      text,
    department   text,
    policy_type  text,
    source       text,
    file_type    text,
    chunk_index  int,
    similarity   float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        pc.id,
        pc.content,
        pc.department,
        pc.policy_type,
        pc.source,
        pc.file_type,
        pc.chunk_index,
        1 - (pc.embedding <=> query_embedding) AS similarity
    FROM policy_chunks pc
    WHERE
        -- Optional department filter (empty string = no filter)
        (filter_dept  = '' OR pc.department  = filter_dept)
        AND
        -- Optional policy type filter (empty string = no filter)
        (filter_ptype = '' OR pc.policy_type = filter_ptype)
    ORDER BY pc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ================================================================
--  VERIFY — you should see 2 tables and 1 function
-- ================================================================
SELECT 'Tables:' AS check;
SELECT table_name
FROM   information_schema.tables
WHERE  table_schema = 'public'
  AND  table_name IN ('policy_chunks','ingested_files')
ORDER  BY table_name;

SELECT 'Functions:' AS check;
SELECT routine_name
FROM   information_schema.routines
WHERE  routine_schema = 'public'
  AND  routine_name   = 'match_policy_chunks';

SELECT '✅ Setup complete! Now run: python fix_and_reindex.py' AS status;
