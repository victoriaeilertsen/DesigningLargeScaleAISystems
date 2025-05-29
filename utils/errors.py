from a2a.types import JSONRPCError

class A2AError(Exception):
    """Base class for A2A errors."""
    def __init__(self, code: int, message: str):
        self.error = JSONRPCError(
            code=code,
            message=message
        )
        super().__init__(message)

class TaskNotFoundError(JSONRPCError):
    """Raised when a task is not found."""
    def __init__(self, task_id: str):
        super().__init__(
            code=-32601,
            message=f"Task not found: {task_id}",
            data={"type": "task_not_found", "task_id": task_id}
        )

class InvalidMessageError(A2AError):
    """Raised when a message is invalid."""
    def __init__(self, message: str):
        super().__init__(-32002, f"Invalid message: {message}")

class AuthenticationError(A2AError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(-32003, message)

class AuthorizationError(A2AError):
    """Raised when authorization fails."""
    def __init__(self, message: str = "Authorization failed"):
        super().__init__(-32004, message)

class RateLimitError(A2AError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(-32005, message)

class ValidationError(JSONRPCError):
    """Raised when input validation fails."""
    def __init__(self, message: str):
        super().__init__(
            code=-32602,
            message=f"Validation error: {message}",
            data={"type": "validation_error"}
        )

class AgentCommunicationError(JSONRPCError):
    """Raised when communication with another agent fails."""
    def __init__(self, message: str):
        super().__init__(
            code=-32000,
            message=f"Agent communication error: {message}",
            data={"type": "agent_communication_error"}
        ) 