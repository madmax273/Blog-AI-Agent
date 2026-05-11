"""
Database initialization script
Run this script to create all tables in the SQLite database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import Base, engine
from database.models import BlogThread, User

def init_db():
    """Initialize the database with all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("Tables created:")
    print("  - blog_threads")
    print("  - users")

if __name__ == "__main__":
    init_db()
