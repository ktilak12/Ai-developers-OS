from orchestrator.state import OrchestratorState, WorkflowStatus, ApprovalState


class AgentRouter:
    """
    Intelligent Router deciding which agent should act next in what order,
    enforcing iteration retry limits and human approval gates.
    """

    @classmethod
    def get_next_step(cls, state: OrchestratorState) -> WorkflowStatus:
        current = state.status

        if current == WorkflowStatus.PENDING:
            return WorkflowStatus.PLANNING

        elif current == WorkflowStatus.PLANNING:
            return WorkflowStatus.RESEARCHING

        elif current == WorkflowStatus.RESEARCHING:
            return WorkflowStatus.CODING

        elif current == WorkflowStatus.CODING:
            return WorkflowStatus.TESTING

        elif current == WorkflowStatus.TESTING:
            if state.test_success:
                return WorkflowStatus.SECURITY_SCAN
            else:
                # Tests failed: check iteration retry limit
                if state.iteration < state.max_iterations:
                    state.iteration += 1
                    return WorkflowStatus.CODING  # Retry fix with error diagnostics
                else:
                    return WorkflowStatus.FAILED  # Max iterations reached

        elif current == WorkflowStatus.SECURITY_SCAN:
            return WorkflowStatus.REVIEWING

        elif current == WorkflowStatus.REVIEWING:
            return WorkflowStatus.WAITING_APPROVAL

        elif current == WorkflowStatus.WAITING_APPROVAL:
            if state.approval_status == ApprovalState.APPROVED:
                return WorkflowStatus.COMPLETED
            elif state.approval_status == ApprovalState.REJECTED:
                return WorkflowStatus.FAILED
            else:
                return WorkflowStatus.WAITING_APPROVAL

        return current
