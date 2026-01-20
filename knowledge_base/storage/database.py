"""
Database wrapper for SQLAlchemy.
Provides database session management and connection utilities.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from contextlib import contextmanager
import os

from knowledge_base.storage.models import Base


class Database:
    """
    Database wrapper for SQLAlchemy.
    """

    def __init__(self, database_url: str = None):
        """
        Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL. Defaults to sqlite:///./data/knowledge_base.db
        """
        if database_url is None:
            # Create data directory if it doesn't exist
            os.makedirs("./data", exist_ok=True)
            database_url = "sqlite:///./data/knowledge_base.db"

        self.database_url = database_url

        # Create engine
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
            echo=False,
        )

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all tables from the database."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy Session object
        """
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Yields:
            SQLAlchemy Session object

        Example:
            with db.session_scope() as session:
                session.add(Document(doc_name="test"))
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database instance
_db_instance = None


def get_database() -> Database:
    """
    Get the global database instance.

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.

    Yields:
        SQLAlchemy Session object
    """
    db = get_database()
    with db.session_scope() as session:
        yield session
