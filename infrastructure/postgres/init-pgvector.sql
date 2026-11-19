-- Initialize PostgreSQL extensions for OpenReview AI
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Verify extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector');
