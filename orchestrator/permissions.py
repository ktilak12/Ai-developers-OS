from enum import Enum
from typing import Dict, Any


class ActionPermission(str, Enum):
    AUTO_ALLOWED = "AUTO_ALLOWED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    FORBIDDEN = "FORBIDDEN"


class PermissionPolicy:
    """
    Human Approval Layer (PDF Module 18):
    Enforces permission gates between safe autonomous developer actions
    and high-impact operations requiring explicit human approval.
    """

    POLICY_MAP: Dict[str, ActionPermission] = {
        "create_branch": ActionPermission.AUTO_ALLOWED,
        "modify_source": ActionPermission.AUTO_ALLOWED,
        "run_tests": ActionPermission.AUTO_ALLOWED,
        "run_sandbox_command": ActionPermission.AUTO_ALLOWED,
        "create_pr": ActionPermission.APPROVAL_REQUIRED,
        "deploy_production": ActionPermission.APPROVAL_REQUIRED,
        "delete_repository": ActionPermission.FORBIDDEN,
        "expose_secrets": ActionPermission.FORBIDDEN,
        "modify_infrastructure": ActionPermission.FORBIDDEN
    }

    @classmethod
    def check_permission(cls, action_name: str) -> ActionPermission:
        return cls.POLICY_MAP.get(action_name, ActionPermission.APPROVAL_REQUIRED)

    @classmethod
    def requires_approval(cls, action_name: str) -> bool:
        return cls.check_permission(action_name) == ActionPermission.APPROVAL_REQUIRED

    @classmethod
    def is_allowed_autonomously(cls, action_name: str) -> bool:
        return cls.check_permission(action_name) == ActionPermission.AUTO_ALLOWED
