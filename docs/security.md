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
