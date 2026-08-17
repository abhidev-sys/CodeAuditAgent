"""
Custom exception hierarchy.

WHY custom exceptions?
- Precise error handling — catch exactly what you expect
- Clear error messages for debugging
- Different HTTP status codes per exception type
- Never silently swallow errors

INTERVIEW ANGLE:
"How do you handle errors in a multi-agent system where each agent can fail?"
→ Typed exception hierarchy, each agent raises specific errors
"""


class CodeAuditBaseException(Exception):
    """Base exception for all CodeAuditAgent errors."""
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class RepositoryError(CodeAuditBaseException):
    """Repository ingestion or validation errors."""
    pass


class UnsupportedLanguageError(RepositoryError):
    """Repository language is not supported."""
    pass


class RepositoryTooLargeError(RepositoryError):
    """Repository exceeds size limits."""
    pass


class AnalysisError(CodeAuditBaseException):
    """Code analysis layer errors."""
    pass


class ASTParsingError(AnalysisError):
    """Tree-sitter AST parsing failed."""
    pass


class AgentError(CodeAuditBaseException):
    """LangGraph agent execution errors."""
    pass


class LLMError(AgentError):
    """LLM call failed or returned malformed output."""
    pass


class LLMTimeoutError(LLMError):
    """LLM call timed out."""
    pass


class PatchError(CodeAuditBaseException):
    """Patch generation or application errors."""
    pass


class VerificationError(CodeAuditBaseException):
    """Patch verification failed."""
    pass


class SandboxError(CodeAuditBaseException):
    """Docker sandbox execution errors."""
    pass


class KnowledgeBaseError(CodeAuditBaseException):
    """RAG knowledge base errors."""
    pass


class ScanNotFoundError(CodeAuditBaseException):
    """Requested scan does not exist."""
    pass