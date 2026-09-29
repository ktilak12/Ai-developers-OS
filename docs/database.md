# Database Schema

Database: PostgreSQL

## Tables

### `users`
- `id` (UUID, PK)
- `name` (String)
- `email` (String)
- `created_at` (Timestamp)

### `projects`
- `id` (UUID, PK)
- `user_id` (UUID, FK to users)
- `name` (String)
- `repository_url` (String)
- `default_branch` (String)
- `language` (String)
- `framework` (String)
- `created_at` (Timestamp)

### `tasks`
- `id` (UUID, PK)
- `project_id` (UUID, FK to projects)
- `title` (String)
- `description` (Text)
- `status` (String)
- `created_at` (Timestamp)
- `completed_at` (Timestamp)

### `agent_runs`
- `id` (UUID, PK)
- `task_id` (UUID, FK to tasks)
- `agent_name` (String)
- `status` (String)
- `started_at` (Timestamp)
- `completed_at` (Timestamp)
- `input_tokens` (Integer)
- `output_tokens` (Integer)

### `tool_calls`
- `id` (UUID, PK)
- `agent_run_id` (UUID, FK to agent_runs)
- `tool_name` (String)
- `arguments` (JSON)
- `result` (Text)
- `status` (String)
- `timestamp` (Timestamp)

### `code_changes`
- `id` (UUID, PK)
- `task_id` (UUID, FK to tasks)
- `file_path` (String)
- `change_type` (String)
- `diff` (Text)

### `test_runs`
- `id` (UUID, PK)
- `task_id` (UUID, FK to tasks)
- `command` (String)
- `status` (String)
- `passed` (Integer)
- `failed` (Integer)
- `logs` (Text)

### `security_findings`
- `id` (UUID, PK)
- `task_id` (UUID, FK to tasks)
- `severity` (String)
- `file` (String)
- `line` (Integer)
- `description` (Text)
- `recommendation` (Text)
- `status` (String)

### `project_decisions`
- `id` (UUID, PK)
- `project_id` (UUID, FK to projects)
- `decision` (Text)
- `reason` (Text)
- `alternatives` (Text)
- `created_at` (Timestamp)
