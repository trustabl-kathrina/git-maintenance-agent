"""Domain errors translated to concise CLI messages."""


class GitMaintenanceAgentError(Exception):
    """Base error for expected command failures."""


class ConsentRequiredError(GitMaintenanceAgentError):
    """Raised when a caller has not explicitly authorized a risky action."""


class UnsafePathError(GitMaintenanceAgentError):
    """Raised when a path escapes the workspace or is sensitive."""


class PatchRejectedError(GitMaintenanceAgentError):
    """Raised when a proposal fails safety or freshness checks."""


class RuntimeConfigurationError(GitMaintenanceAgentError):
    """Raised when a live model invocation cannot be configured safely."""
