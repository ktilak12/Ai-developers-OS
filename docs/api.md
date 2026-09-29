# API Specification

Backend API using FastAPI.

## Endpoints

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Connect a new repository
- `GET /api/projects/{id}` - Get project details

### Tasks
- `GET /api/projects/{id}/tasks` - List tasks
- `POST /api/projects/{id}/tasks` - Create a new task (starts orchestrator)
- `GET /api/tasks/{id}` - Get task status and details

### Agents & Execution
- `GET /api/tasks/{id}/runs` - Get agent runs for a task
- `GET /api/tasks/{id}/diff` - Get generated code diffs
- `POST /api/tasks/{id}/approve` - Approve changes and create PR
- `POST /api/tasks/{id}/retry` - Reject changes and instruct AI to try again

### Observability
- `GET /api/metrics` - Get system usage metrics (tokens, success rate)
- `GET /api/traces/{task_id}` - Get execution trace
