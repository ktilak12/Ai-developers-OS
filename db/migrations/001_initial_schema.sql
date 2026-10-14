-- =============================================================================
-- AI Developer OS — PostgreSQL + pgvector Migration Scripts
-- Run these in order against your PostgreSQL 15+ database.
--
-- Prerequisites:
--   1. CREATE DATABASE aideveloperos;
--   2. \c aideveloperos
--   3. Run this file: psql -d aideveloperos -f migrations/001_initial_schema.sql
-- =============================================================================

-- Enable pgvector extension (requires PostgreSQL 15+ with pgvector installed)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- for full-text similarity

-- =============================================================================
-- Schema versioning
-- =============================================================================
CREATE TABLE IF NOT EXISTS schema_migrations (
    version         VARCHAR(50) PRIMARY KEY,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description     TEXT
);

INSERT INTO schema_migrations (version, description)
VALUES ('001', 'Initial AI Developer OS schema')
ON CONFLICT (version) DO NOTHING;

-- =============================================================================
-- Projects
-- =============================================================================
CREATE TABLE IF NOT EXISTS projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    github_repo_url TEXT,
    root_path       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_name ON projects USING btree (name);

-- =============================================================================
-- Code Chunks (RAG Embeddings)
-- 1536 dims for text-embedding-3-small (OpenAI)
-- 768 dims for models/text-embedding-004 (Gemini)
-- Adjust VECTOR dimension below to match your embedding model.
-- =============================================================================
CREATE TABLE IF NOT EXISTS code_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path       TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    language        VARCHAR(50),
    -- Change 768 to 1536 if using OpenAI text-embedding-3-small
    embedding       VECTOR(768),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, file_path, chunk_index)
);

-- HNSW index for fast approximate nearest-neighbor search
CREATE INDEX IF NOT EXISTS idx_code_chunks_embedding
    ON code_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_code_chunks_project ON code_chunks USING btree (project_id);
CREATE INDEX IF NOT EXISTS idx_code_chunks_file ON code_chunks USING btree (file_path);
-- Full-text index for hybrid search
CREATE INDEX IF NOT EXISTS idx_code_chunks_content ON code_chunks USING gin (to_tsvector('english', content));

-- =============================================================================
-- AST Symbols Index
-- =============================================================================
CREATE TABLE IF NOT EXISTS ast_symbols (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path       TEXT NOT NULL,
    symbol_name     VARCHAR(500) NOT NULL,
    symbol_type     VARCHAR(50) NOT NULL,  -- function | class | route | model | component | struct | trait
    language        VARCHAR(50),
    line_number     INTEGER,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ast_symbols_project ON ast_symbols USING btree (project_id);
CREATE INDEX IF NOT EXISTS idx_ast_symbols_name ON ast_symbols USING gin (symbol_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_ast_symbols_type ON ast_symbols USING btree (symbol_type);

-- =============================================================================
-- Project Memory — Architecture Records
-- =============================================================================
CREATE TABLE IF NOT EXISTS architecture_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    component       VARCHAR(255) NOT NULL,
    description     TEXT,
    tech_stack      JSONB DEFAULT '[]',
    design_patterns JSONB DEFAULT '[]',
    constraints     JSONB DEFAULT '[]',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Project Memory — Architecture Decision Records (ADRs)
-- =============================================================================
CREATE TABLE IF NOT EXISTS decision_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL,
    context         TEXT,
    decision        TEXT,
    consequences    TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'accepted',  -- proposed | accepted | deprecated | superseded
    tags            JSONB DEFAULT '[]',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_project ON decision_records USING btree (project_id);
CREATE INDEX IF NOT EXISTS idx_decisions_status ON decision_records USING btree (status);

-- =============================================================================
-- Project Memory — Task History
-- =============================================================================
CREATE TABLE IF NOT EXISTS task_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_request    TEXT NOT NULL,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending | running | completed | failed
    agent_results   JSONB DEFAULT '{}',
    files_modified  JSONB DEFAULT '[]',
    test_result     JSONB DEFAULT '{}',
    security_result JSONB DEFAULT '{}',
    review_result   JSONB DEFAULT '{}',
    pr_url          TEXT,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_task_history_project ON task_history USING btree (project_id);
CREATE INDEX IF NOT EXISTS idx_task_history_status ON task_history USING btree (status);
CREATE INDEX IF NOT EXISTS idx_task_history_created ON task_history USING btree (created_at DESC);

-- =============================================================================
-- Project Memory — Developer Preferences
-- =============================================================================
CREATE TABLE IF NOT EXISTS developer_preferences (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category        VARCHAR(100) NOT NULL,  -- code_style | testing | security | tooling | architecture
    preference_key  VARCHAR(255) NOT NULL,
    preference_value TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, category, preference_key)
);

-- =============================================================================
-- Observability — Workflow Traces
-- =============================================================================
CREATE TABLE IF NOT EXISTS workflow_traces (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID REFERENCES projects(id) ON DELETE SET NULL,
    trace_id        VARCHAR(100) UNIQUE NOT NULL,
    task_request    TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'running',
    total_duration_ms BIGINT,
    total_cost_usd  NUMERIC(10, 6) DEFAULT 0,
    agent_spans     JSONB DEFAULT '[]',
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_traces_project ON workflow_traces USING btree (project_id);
CREATE INDEX IF NOT EXISTS idx_traces_status ON workflow_traces USING btree (status);
CREATE INDEX IF NOT EXISTS idx_traces_created ON workflow_traces USING btree (created_at DESC);

-- =============================================================================
-- GitHub Integration — Connected Repositories
-- =============================================================================
CREATE TABLE IF NOT EXISTS github_repositories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    github_repo_id  BIGINT UNIQUE,
    owner           VARCHAR(255) NOT NULL,
    repo_name       VARCHAR(255) NOT NULL,
    default_branch  VARCHAR(100) DEFAULT 'main',
    installation_id BIGINT,
    access_token_encrypted TEXT,  -- store encrypted, never plaintext
    webhook_active  BOOLEAN DEFAULT FALSE,
    last_synced_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (owner, repo_name)
);

CREATE INDEX IF NOT EXISTS idx_github_repos_project ON github_repositories USING btree (project_id);

-- =============================================================================
-- CI/CD Workflow Definitions
-- =============================================================================
CREATE TABLE IF NOT EXISTS cicd_workflows (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    trigger         VARCHAR(100) NOT NULL,  -- push | pull_request | schedule | manual
    workflow_yaml   TEXT NOT NULL,          -- the generated GitHub Actions YAML
    language        VARCHAR(50),
    framework       VARCHAR(100),
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- Helper function: auto-update updated_at
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Attach trigger to all tables with updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'projects', 'architecture_records', 'decision_records',
        'developer_preferences', 'cicd_workflows'
    ]
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_updated_at ON %I;
             CREATE TRIGGER trg_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();',
            t, t
        );
    END LOOP;
END;
$$;
