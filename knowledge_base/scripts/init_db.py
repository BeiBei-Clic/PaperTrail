"""
Database initialization script for knowledge base.
Creates the database schema and initializes necessary data.
"""

import sys
import os
import logging

# Add parent directory to path to import from knowledge_base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_base.storage.database import get_database
from knowledge_base.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database(drop_existing: bool = False):
    """
    Initialize the database.

    Args:
        drop_existing: If True, drop existing tables before creating new ones
    """
    settings = get_settings()
    db = get_database()

    logger.info(f"Initializing database at: {settings.database_url}")

    if drop_existing:
        logger.warning("Dropping existing tables...")
        db.drop_tables()

    logger.info("Creating tables...")
    db.create_tables()

    logger.info("Database initialized successfully!")


def main():
    """Main entry point for database initialization."""
    import argparse

    parser = argparse.ArgumentParser(description="Initialize knowledge base database")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating new ones"
    )

    args = parser.parse_args()

    try:
        init_database(drop_existing=args.drop)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
