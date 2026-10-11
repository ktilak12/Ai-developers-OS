# Security Model

## Execution Sandbox
All code modifications and test executions occur inside a secure Docker container.
The AI is NEVER allowed to execute arbitrary commands on the host machine.

### Sandbox Constraints
- **CPU Limits:** Configured per container.
- **Memory Limits:** Configured per container to prevent OOM.
- **Execution Timeout:** Strict limits on command execution time.
- **Restricted Filesystem:** Only the project sandbox directory is mounted.
- **Network Access:** Controlled/blocked unless required for dependencies.
- **Container Cleanup:** Ephemeral containers that are destroyed after the task.

## Human Approval Layer
The AI cannot automatically perform critical actions without human consent.
- ❌ Push production code
- ❌ Delete repositories
- ❌ Expose secrets
- ❌ Deploy applications
- ❌ Modify infrastructure

**Required Approvals:**
- Creating a PR requires developer review of the diff.
- Deploying to production requires explicit human approval.

## Autonomous Agent Safeguards (Phases 14-16)
- **Multi-Agent Human Gate:** Routine `auto_approve` is automatically revoked if the Security Agent detects `CRITICAL`/`HIGH` vulnerabilities, test failures, or review rejections.
- **Trace Credential Redaction:** Passwords, API keys, Bearer tokens, and Authorization headers are automatically redacted from observability traces.
- **Path Traversal Defenses:** Storage and evaluation state locations are verified against canonical project realpaths.
- **Input Sanitization:** Benchmark IDs and reports enforce strict regex validation and HTML escaping to prevent injection attacks.

