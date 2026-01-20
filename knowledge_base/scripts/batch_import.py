"""
Batch import script for knowledge base.
Import multiple documents from a directory into the knowledge base.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List
import logging

# Add parent directory to path to import from knowledge_base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_base.storage.database import get_database
from knowledge_base.storage.file_storage import FileStorage
from knowledge_base.core.document_manager import DocumentManager
from knowledge_base.core.index_engine import IndexEngine
from knowledge_base.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def batch_import_documents(
    directory: str,
    doc_type: str = "auto",
    index: bool = True,
    recursive: bool = False
) -> dict:
    """
    Batch import documents from a directory.

    Args:
        directory: Path to directory containing documents
        doc_type: Document type ('auto', 'pdf', 'markdown')
        index: Whether to index documents after import
        recursive: Whether to recursively search subdirectories

    Returns:
        Dictionary with import results
    """
    db = get_database()
    session = db.get_session()

    try:
        settings = get_settings()
        file_storage = FileStorage(settings.storage_path)
        doc_manager = DocumentManager(session, file_storage)
        index_engine = IndexEngine(session) if index else None

        results = {
            "successful": [],
            "failed": [],
            "skipped": [],
        }

        # Find documents
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.error(f"Directory not found: {directory}")
            return results

        # Get files based on document type
        if doc_type == "auto":
            patterns = ["*.pdf", "*.md", "*.markdown"]
        elif doc_type == "pdf":
            patterns = ["*.pdf"]
        elif doc_type == "markdown":
            patterns = ["*.md", "*.markdown"]
        else:
            logger.error(f"Invalid document type: {doc_type}")
            return results

        files = []
        if recursive:
            for pattern in patterns:
                files.extend(dir_path.rglob(pattern))
        else:
            for pattern in patterns:
                files.extend(dir_path.glob(pattern))

        logger.info(f"Found {len(files)} documents to import")

        # Import each document
        for file_path in files:
            try:
                # Determine document type
                if file_path.suffix.lower() == '.pdf':
                    current_doc_type = 'pdf'
                elif file_path.suffix.lower() in ['.md', '.markdown']:
                    current_doc_type = 'markdown'
                else:
                    results["skipped"].append(str(file_path))
                    logger.warning(f"Skipped unknown file type: {file_path}")
                    continue

                logger.info(f"Importing: {file_path}")

                # Add document
                document = doc_manager.add_document(
                    file_path=str(file_path),
                    doc_type=current_doc_type,
                    doc_name=file_path.name
                )

                results["successful"].append({
                    "id": document.id,
                    "name": document.doc_name,
                    "path": str(file_path),
                })

                # Index if requested
                if index_engine:
                    logger.info(f"Indexing: {file_path}")
                    page_index = index_engine.index_document(document.id)
                    if page_index:
                        logger.info(f"  Indexed {page_index.total_nodes} nodes, depth {page_index.max_depth}")
                    else:
                        logger.warning(f"  Indexing failed for {file_path}")

            except FileExistsError:
                logger.warning(f"Document already exists: {file_path}")
                results["skipped"].append(str(file_path))
            except Exception as e:
                logger.error(f"Failed to import {file_path}: {e}")
                results["failed"].append({
                    "path": str(file_path),
                    "error": str(e),
                })

        # Print summary
        logger.info("\n" + "="*50)
        logger.info("Batch Import Summary")
        logger.info("="*50)
        logger.info(f"Successful: {len(results['successful'])}")
        logger.info(f"Failed:     {len(results['failed'])}")
        logger.info(f"Skipped:    {len(results['skipped'])}")

        if results["failed"]:
            logger.warning("\nFailed documents:")
            for item in results["failed"]:
                logger.warning(f"  - {item['path']}: {item['error']}")

        return results

    finally:
        session.close()


def main():
    """Main entry point for batch import."""
    parser = argparse.ArgumentParser(
        description="Batch import documents into PageIndex Knowledge Base"
    )
    parser.add_argument(
        "directory",
        help="Path to directory containing documents to import"
    )
    parser.add_argument(
        "--type",
        choices=["auto", "pdf", "markdown"],
        default="auto",
        help="Document type to import (default: auto)"
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Don't index documents after import"
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recursively import from subdirectories"
    )

    args = parser.parse_args()

    try:
        batch_import_documents(
            directory=args.directory,
            doc_type=args.type,
            index=not args.no_index,
            recursive=args.recursive
        )
    except Exception as e:
        logger.error(f"Batch import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
