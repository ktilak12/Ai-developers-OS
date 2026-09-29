# Agent Architecture

The AI Developer OS uses a multi-agent architecture coordinated by an Orchestrator.

## Agents

### 1. Planner Agent
- **Role:** Understands the task and creates an implementation plan.
- **Inputs:** User request, repository context (RAG/Graph).
- **Outputs:** Step-by-step implementation plan.

### 2. Coder Agent
- **Role:** Modifies code based on the plan.
- **Tools:** `read_file`, `write_file`, `edit_file`, `search_code`, `list_files`, `find_symbol`.
- **Outputs:** Code diffs.

### 3. Testing Agent
- **Role:** Runs tests in the secure sandbox to validate changes.
- **Tools:** `npm test`, `pytest`, etc.
- **Outputs:** Test results, failure analysis.

### 4. Security Agent
- **Role:** Checks for vulnerabilities, hardcoded secrets, dangerous commands.
- **Outputs:** Security report (severity, file, problem, recommendation).

### 5. Research Agent
- **Role:** Investigates external technical knowledge (APIs, migration guides).
- **Outputs:** Summarized research findings.

### 6. Reviewer Agent
- **Role:** Acts as a second pair of eyes, reviews architecture, tests, security, performance.
- **Outputs:** Code review with suggestions.
