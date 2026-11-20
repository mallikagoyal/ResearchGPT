"""Declarative base class shared by all ORM models.

Importing this module (directly or transitively via app.models) registers
model metadata used by Alembic autogeneration.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass
