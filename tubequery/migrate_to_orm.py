#!/usr/bin/env python3
"""
Migration Script: Raw SQL to SQLAlchemy ORM
==========================================
Helps migrate from raw Supabase queries to SQLAlchemy ORM.
"""

import os
import sys
import re
from pathlib import Path

def update_imports_in_file(file_path: Path) -> bool:
    """Update database imports in a Python file."""
    if not file_path.exists() or file_path.suffix != '.py':
        return False
    
    content = file_path.read_text()
    original_content = content
    
    # Replace import statements
    patterns = [
        (r'from api\.db import', 'from api.db_orm import'),
        (r'import api\.db as db', 'import api.db_orm as db'),
    ]
    
    for old_pattern, new_pattern in patterns:
        content = re.sub(old_pattern, new_pattern, content)
    
    if content != original_content:
        file_path.write_text(content)
        return True
    return False

def main():
    """Run the migration."""
    print("🔄 Migrating TubeQuery to SQLAlchemy ORM...")
    
    # Check if we're in the right directory
    if not Path("api").exists() or not Path("models").exists():
        print("❌ Please run this script from the tubequery/ directory")
        sys.exit(1)
    
    # Update router files
    router_dir = Path("api/routers")
    updated_files = []
    
    if router_dir.exists():
        for router_file in router_dir.glob("*.py"):
            if update_imports_in_file(router_file):
                updated_files.append(str(router_file))
    
    # Update other API files
    api_files = ["api/main.py", "api/dependencies.py"]
    for api_file in api_files:
        file_path = Path(api_file)
        if update_imports_in_file(file_path):
            updated_files.append(api_file)
    
    if updated_files:
        print("✅ Updated import statements in:")
        for file in updated_files:
            print(f"   - {file}")
    else:
        print("ℹ️  No import statements needed updating")
    
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install sqlalchemy alembic psycopg2-binary")
    print("2. Set DATABASE_URL environment variable")
    print("3. Initialize database: python init_db.py")
    print("4. Test your API endpoints")
    print("5. Read MIGRATION_GUIDE.md for detailed information")
    
    print("\n⚠️  Important:")
    print("- Backup your database before running init_db.py")
    print("- Test in development environment first")
    print("- The old api/db.py is kept for reference")

if __name__ == "__main__":
    main()