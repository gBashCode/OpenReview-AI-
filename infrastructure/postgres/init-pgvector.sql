-- ==============================================================================
-- OpenReview AI - PostgreSQL & pgvector Database Initialization
-- ==============================================================================

-- Core UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vector similarity search (Cosine, L2, Dot product)
CREATE EXTENSION IF NOT EXISTS "vector";

-- Trigram indexing for fuzzy text and symbol keyword retrieval
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- B-tree GIST for hybrid multi-column index acceleration
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Verify extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector', 'pg_trgm', 'btree_gist');
