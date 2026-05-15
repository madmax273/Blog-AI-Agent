"""
Migration script to add image_urls column to blog_threads table
Run this script to add the new column without losing existing data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import engine
from sqlalchemy import text

def migrate():
    """Add image_urls column to blog_threads table"""
    print("Adding image_urls column to blog_threads table...")

    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(blog_threads)"))
        columns = [row[1] for row in result.fetchall()]

        if 'image_urls' in columns:
            print("Column image_urls already exists. Skipping migration.")
            return

        # Add the column
        conn.execute(text("ALTER TABLE blog_threads ADD COLUMN image_urls JSON"))
        conn.commit()
        print("Successfully added image_urls column to blog_threads table")

if __name__ == "__main__":
    migrate()
