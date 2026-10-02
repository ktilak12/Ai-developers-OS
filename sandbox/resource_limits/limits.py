from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ResourceLimits:
    """
    Defines strict resource bounds for isolated sandbox container execution.
    Prevents CPU monopolization, OOM conditions, and long-running hangs.
    """
    cpu_limit: float = 1.5          # Number of CPU cores (e.g., 1.5 CPUs)
    memory_limit: str = "512m"      # Maximum RAM (512 Megabytes)
    memory_swap: str = "512m"       # Prevent unbounded swap usage
    execution_timeout: int = 60     # Maximum execution time in seconds
    pids_limit: int = 128           # Prevent fork bombs
    network_mode: str = "none"      # Network isolation ("none" or "bridge")
    read_only_rootfs: bool = False  # Container root filesystem
    tmpfs_size: str = "64m"         # Size of temporary in-memory write buffer

    def to_docker_run_args(self) -> list[str]:
        """Convert constraints into docker run CLI arguments."""
        args = [
            f"--cpus={self.cpu_limit}",
            f"--memory={self.memory_limit}",
            f"--memory-swap={self.memory_swap}",
            f"--pids-limit={self.pids_limit}",
            f"--network={self.network_mode}",
        ]
        if self.read_only_rootfs:
            args.append("--read-only")
        if self.tmpfs_size:
            args.extend(["--tmpfs", f"/tmp:size={self.tmpfs_size},exec"])
        return args

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_limit": self.cpu_limit,
            "memory_limit": self.memory_limit,
            "memory_swap": self.memory_swap,
            "execution_timeout": self.execution_timeout,
            "pids_limit": self.pids_limit,
            "network_mode": self.network_mode,
            "read_only_rootfs": self.read_only_rootfs,
            "tmpfs_size": self.tmpfs_size
        }

DEFAULT_SANDBOX_LIMITS = ResourceLimits()
