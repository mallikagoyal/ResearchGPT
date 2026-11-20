"""FastAPI dependencies for authentication and dependency injection.

Centralizes how repositories/services are constructed per-request, and
provides the `get_current_user` dependency used to protect routes.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService

# tokenUrl is only used to populate the Swagger UI "Authorize" form; the
# actual login endpoint accepts a JSON body, not this OAuth2 form spec.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Provide a UserRepository bound to the current request's DB session."""
    return UserRepository(db)


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """Provide an AuthService with its repository dependency injected."""
    return AuthService(user_repository)


def get_document_repository(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    """Provide a DocumentRepository bound to the current request's DB session."""
    return DocumentRepository(db)


def get_document_chunk_repository(db: AsyncSession = Depends(get_db)) -> DocumentChunkRepository:
    """Provide a DocumentChunkRepository bound to the current request's DB session."""
    return DocumentChunkRepository(db)


def get_document_service(
    document_repository: DocumentRepository = Depends(get_document_repository),
    chunk_repository: DocumentChunkRepository = Depends(get_document_chunk_repository),
) -> DocumentService:
    """Provide a DocumentService with its repository dependencies injected."""
    return DocumentService(document_repository, chunk_repository)


def get_conversation_repository(db: AsyncSession = Depends(get_db)) -> ConversationRepository:
    """Provide a ConversationRepository bound to the current request's DB session."""
    return ConversationRepository(db)


def get_message_repository(db: AsyncSession = Depends(get_db)) -> MessageRepository:
    """Provide a MessageRepository bound to the current request's DB session."""
    return MessageRepository(db)


def get_conversation_service(
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    message_repository: MessageRepository = Depends(get_message_repository),
) -> ConversationService:
    """Provide a ConversationService with its repository dependencies injected."""
    return ConversationService(conversation_repository, message_repository)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    """Resolve the current authenticated user from the Authorization header.

    Raises:
        HTTPException(401): If the token is missing, invalid, expired, or
            no longer maps to an existing/active user.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise unauthorized

    user_id_str = decode_access_token(token)
    if user_id_str is None:
        raise unauthorized

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise unauthorized from exc

    user = await user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise unauthorized

    return user
