# Migration Guide: Raw SQL to SQLAlchemy ORM

## Why Migrate to ORM?

The current codebase uses raw SQL queries through the Supabase client, which has several drawbacks:

### Current Issues
- **No Type Safety**: Queries are strings, no compile-time validation
- **SQL Injection Risk**: Even with parameterized queries, it's error-prone
- **Manual Schema Management**: Schema changes require manual updates everywhere
- **No Relationship Management**: Manual handling of foreign keys and joins
- **Testing Difficulties**: Hard to mock database operations
- **Maintenance Overhead**: Schema changes break code in unpredictable ways

### Benefits of SQLAlchemy ORM
- **Type Safety**: Models define schema, catch errors at development time
- **Automatic Migrations**: Schema changes are versioned with Alembic
- **Relationship Management**: Automatic handling of foreign keys and cascades
- **Query Builder**: Safer, more readable queries
- **Connection Pooling**: Better performance and resource management
- **Testing**: Easy to mock and test with in-memory databases
- **IDE Support**: Better autocomplete and refactoring

## Migration Strategy

### Phase 1: Setup ORM Infrastructure ✅
- [x] Create SQLAlchemy models (`models/database.py`)
- [x] Setup database configuration (`database.py`)
- [x] Create database service layer (`services/database_service.py`)
- [x] Setup Alembic for migrations
- [x] Create initial migration script
- [x] Add ORM dependencies to requirements.txt

### Phase 2: Create Compatibility Layer ✅
- [x] Create ORM-based adapter (`api/db_orm.py`) that provides the same interface as the old `api/db.py`
- [x] This allows existing routers to work without changes while using ORM underneath

### Phase 3: Database Migration
1. **Backup your current database**
2. **Install new dependencies**:
   ```bash
   pip install sqlalchemy alembic psycopg2-binary
   ```
3. **Set DATABASE_URL environment variable**:
   ```bash
   # For PostgreSQL (Supabase)
   DATABASE_URL=postgresql://user:password@host:port/database
   ```
4. **Run the initialization script**:
   ```bash
   python init_db.py
   ```

### Phase 4: Update Import Statements
Replace the old database imports in your routers:

```python
# OLD
from api.db import upsert_user, get_user, save_source, list_sources

# NEW  
from api.db_orm import upsert_user, get_user, save_source, list_sources
```

### Phase 5: Gradual Router Migration (Optional)
For better type safety and modern patterns, gradually update routers to use the ORM directly:

```python
# OLD - Raw Supabase queries
@router.get("/sources")
def get_sources(user: dict = Depends(get_current_user), db: Any = Depends(get_supabase)):
    result = db.table("sources").select("*").eq("user_id", user["uid"]).execute()
    return result.data

# NEW - ORM with dependency injection
@router.get("/sources")
def get_sources(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db_service = DatabaseService(db)
    sources = db_service.list_sources(user["uid"])
    return [source_to_dict(s) for s in sources]
```

## File Structure After Migration

```
tubequery/
├── models/
│   └── database.py          # SQLAlchemy models
├── services/
│   └── database_service.py  # High-level database operations
├── api/
│   ├── db.py               # OLD - Raw SQL (keep for reference)
│   └── db_orm.py           # NEW - ORM adapter (same interface)
├── alembic/
│   ├── versions/           # Migration scripts
│   ├── env.py             # Alembic environment
│   └── script.py.mako     # Migration template
├── database.py             # Database configuration
├── alembic.ini            # Alembic configuration
└── init_db.py             # Database initialization script
```

## Key Differences

### Schema Definition
```python
# OLD - Manual SQL in migration files
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT,
    ...
);

# NEW - Declarative models
class Source(Base):
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user_profiles.uid", ondelete="CASCADE"))
    title = Column(String)
    
    # Relationships are automatically handled
    user = relationship("UserProfile", back_populates="sources")
```

### Database Operations
```python
# OLD - Raw queries
result = db.table("sources").select("*").eq("user_id", user_id).execute()
sources = result.data

# NEW - ORM queries
sources = db.query(Source).filter_by(user_id=user_id).all()
```

### Migrations
```python
# OLD - Manual SQL scripts
-- Add column manually
ALTER TABLE sources ADD COLUMN new_field TEXT;

# NEW - Automatic migrations
# 1. Update model
class Source(Base):
    new_field = Column(String)

# 2. Generate migration
alembic revision --autogenerate -m "Add new_field to sources"

# 3. Apply migration
alembic upgrade head
```

## Testing the Migration

1. **Backup your database** before running any migrations
2. **Test in development** environment first
3. **Run the initialization script**: `python init_db.py`
4. **Verify all endpoints** still work correctly
5. **Check data integrity** after migration

## Rollback Plan

If issues occur:
1. **Restore database** from backup
2. **Revert import statements** back to `api.db`
3. **Remove ORM dependencies** if needed

## Future Benefits

After migration, you'll be able to:
- **Generate migrations automatically** when models change
- **Use type hints** for better IDE support
- **Write safer queries** with compile-time validation
- **Test database operations** more easily
- **Scale better** with connection pooling
- **Maintain relationships** automatically

## Commands Reference

```bash
# Initialize database
python init_db.py

# Generate new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current migration status
alembic current

# View migration history
alembic history
```