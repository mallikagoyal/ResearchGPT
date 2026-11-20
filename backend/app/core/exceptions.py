"""Domain-level exceptions.

Services and repositories raise these instead of raw HTTPExceptions, so
business logic stays framework-agnostic. The API layer (see
app/api/error_handlers.py, added in a later phase) translates them into
proper HTTP responses in one centralized place.
"""


class ResearchGPTError(Exception):
    """Base class for all application-specific errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(ResearchGPTError):
    """Raised when a requested resource does not exist."""


class AlreadyExistsError(ResearchGPTError):
    """Raised when attempting to create a resource that already exists."""


class InvalidCredentialsError(ResearchGPTError):
    """Raised when authentication credentials are invalid."""


class UnauthorizedError(ResearchGPTError):
    """Raised when a user attempts an action they are not permitted to do."""


class ValidationFailedError(ResearchGPTError):
    """Raised when input fails domain-level validation."""


class FileProcessingError(ResearchGPTError):
    """Raised when document parsing/chunking/embedding fails."""
