# Database Migrations Guide

This document describes how to manage database schema changes using Alembic migrations in the Planted application.

## Overview

Planted uses [Alembic](https://alembic.sqlalchemy.org/) for database version control and migrations. Alembic provides:
- **Version control** for database schema changes
- **Forward migrations** (upgrade) to apply new schema changes
- **Backward migrations** (downgrade) to rollback changes
- **Migration history** tracking via the `alembic_version` table

## Migration Directory Structure

```
Planted/
├── alembic/                    # Alembic migration directory
│   ├── versions/              # Migration scripts
│   │   └── e01efa1a265a_initial_schema.py
│   ├── env.py                 # Alembic environment configuration
│   ├── script.py.mako         # Template for new migrations
│   └── README                 # Alembic information
├── alembic.ini                # Alembic configuration file
└── garden.db                  # SQLite database file
```

## Configuration

The database connection is configured in `alembic.ini`:

```ini
sqlalchemy.url = sqlite:///garden.db
```

This points to the SQLite database file `garden.db` in the project root directory.

## Common Migration Operations

### 1. Check Current Migration Version

To see which migration version the database is currently at:

```bash
alembic current
```

### 2. View Migration History

To see all available migrations:

```bash
alembic history --verbose
```

### 3. Apply Migrations (Upgrade)

To upgrade to the latest schema version:

```bash
alembic upgrade head
```

To upgrade to a specific version:

```bash
alembic upgrade <revision_id>
```

To upgrade by one version:

```bash
alembic upgrade +1
```

### 4. Rollback Migrations (Downgrade)

To rollback all migrations:

```bash
alembic downgrade base
```

To rollback to a specific version:

```bash
alembic downgrade <revision_id>
```

To rollback by one version:

```bash
alembic downgrade -1
```

### 5. Create a New Migration

To create a new empty migration:

```bash
alembic revision -m "Description of changes"
```

This creates a new file in `alembic/versions/` with `upgrade()` and `downgrade()` functions that you'll need to implement.

### 6. View Migration SQL (Dry Run)

To see the SQL that would be executed without applying it:

```bash
alembic upgrade head --sql
```

## Creating Migrations

When creating a new migration, you need to manually write the `upgrade()` and `downgrade()` functions. Here's an example:

```python
def upgrade() -> None:
    """Apply schema changes."""
    # Add a new column
    op.add_column('plants', sa.Column('new_field', sa.Text(), nullable=True))
    
    # Create an index
    op.create_index('idx_plants_new_field', 'plants', ['new_field'])


def downgrade() -> None:
    """Revert schema changes."""
    # Drop the index first
    op.drop_index('idx_plants_new_field', 'plants')
    
    # Remove the column
    op.drop_column('plants', 'new_field')
```

### Common Operations

#### Adding a Column

```python
op.add_column('table_name', sa.Column('column_name', sa.Text(), nullable=True))
```

#### Removing a Column

```python
op.drop_column('table_name', 'column_name')
```

#### Creating a Table

```python
op.create_table(
    'new_table',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
)
```

#### Dropping a Table

```python
op.drop_table('table_name')
```

#### Creating an Index

```python
op.create_index('idx_table_column', 'table_name', ['column_name'])
```

#### Dropping an Index

```python
op.drop_index('idx_table_column', 'table_name')
```

## Best Practices

### 1. Always Create Both Upgrade and Downgrade

Every migration should have both `upgrade()` and `downgrade()` functions. This allows you to roll back changes if something goes wrong.

### 2. Test Migrations Before Deployment

Always test migrations on a copy of production data before applying them to production:

```bash
# Copy production database
cp garden.db garden_test.db

# Test on copy (update alembic.ini temporarily to point to garden_test.db)
alembic upgrade head

# Verify the schema and data
sqlite3 garden_test.db ".schema"

# Test rollback
alembic downgrade -1
```

### 3. Backup Before Migrations

**Always backup your database before running migrations**, especially in production. See the [Pre-Migration Backup Script](#pre-migration-backup-script) section below.

### 4. Make Incremental Changes

Create small, focused migrations rather than large, complex ones. This makes them easier to understand, test, and rollback if needed.

### 5. Handle Data Migrations Carefully

When migrations involve data transformations:
- Add new columns with default values
- Migrate data in batches if dealing with large datasets
- Test thoroughly with production-like data

### 6. Document Complex Migrations

Add detailed comments in the migration file explaining:
- Why the change is being made
- Any data transformations performed
- Potential side effects or considerations

### 7. Never Modify Existing Migrations

Once a migration has been applied to production, **never modify it**. Instead, create a new migration to make additional changes. This prevents inconsistencies between environments.

### 8. Review Generated SQL

Before applying a migration, review the SQL it will execute:

```bash
alembic upgrade head --sql > migration.sql
cat migration.sql
```

## Handling Migration Failures

If a migration fails:

1. **Check the error message** - It usually indicates what went wrong
2. **Verify database state** - Check which migrations have been applied:
   ```bash
   alembic current
   sqlite3 garden.db ".schema"
   ```
3. **Rollback if possible**:
   ```bash
   alembic downgrade -1
   ```
4. **Fix the migration** - Create a new migration to fix the issue
5. **Restore from backup** - If the database is in a bad state, restore from your backup

## Pre-Migration Backup Script

Before running migrations, especially in production, **always create a backup**. Here's a recommended backup workflow:

### Manual Backup

```bash
# Create a timestamped backup
cp garden.db "garden.db.backup.$(date +%Y%m%d_%H%M%S)"
```

### Backup Script

Create a file `scripts/backup_database.sh`:

```bash
#!/bin/bash
# Database backup script for Planted

# Configuration
DB_FILE="garden.db"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_FILE}.${TIMESTAMP}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Create backup
echo "Creating backup: ${BACKUP_FILE}"
cp "${DB_FILE}" "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "Backup created successfully"
    
    # Keep only last 10 backups
    ls -t "${BACKUP_DIR}/${DB_FILE}."* | tail -n +11 | xargs -r rm
    echo "Old backups cleaned up (keeping last 10)"
else
    echo "Backup failed!"
    exit 1
fi
```

Make it executable:

```bash
chmod +x scripts/backup_database.sh
```

### Migration Workflow with Backup

```bash
# 1. Backup database
./scripts/backup_database.sh

# 2. Check current version
alembic current

# 3. View pending migrations
alembic history

# 4. Review SQL to be executed (optional)
alembic upgrade head --sql

# 5. Apply migrations
alembic upgrade head

# 6. Verify the migration
alembic current
sqlite3 garden.db ".schema"

# 7. Test the application
python3 main.py
```

## Deployment Workflow

When deploying new code with migrations:

1. **Stop the application**
   ```bash
   # For systemd service
   sudo systemctl stop planted
   
   # Or kill the process
   pkill -f "python.*main.py"
   ```

2. **Backup the database**
   ```bash
   ./scripts/backup_database.sh
   ```

3. **Pull latest code**
   ```bash
   git pull origin main
   ```

4. **Install dependencies** (if updated)
   ```bash
   pip install -r requirements.txt
   ```

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Verify migration succeeded**
   ```bash
   alembic current
   ```

7. **Start the application**
   ```bash
   # For systemd service
   sudo systemctl start planted
   
   # Or run manually
   python3 main.py
   ```

8. **Verify application is working**
   ```bash
   curl http://localhost:5000
   ```

## SQLite-Specific Considerations

### Foreign Key Constraints

SQLite doesn't enforce foreign key constraints by default. Alembic migrations will create them, but they won't be enforced unless you enable them:

```python
# In your application code
conn.execute("PRAGMA foreign_keys = ON")
```

### Limited ALTER TABLE Support

SQLite has limited `ALTER TABLE` support. It cannot:
- Drop columns (in older SQLite versions)
- Modify column types
- Add constraints to existing columns

For these operations, you need to:
1. Create a new table with the desired schema
2. Copy data from the old table
3. Drop the old table
4. Rename the new table

Example:

```python
def upgrade():
    # Create new table with modified schema
    op.create_table(
        'plants_new',
        # ... new schema ...
    )
    
    # Copy data
    op.execute("""
        INSERT INTO plants_new (id, name, ...)
        SELECT id, name, ... FROM plants
    """)
    
    # Drop old table
    op.drop_table('plants')
    
    # Rename new table
    op.rename_table('plants_new', 'plants')
```

## Troubleshooting

### "Target database is not up to date"

This error occurs when trying to create a migration while the database isn't at the latest version. Fix:

```bash
alembic upgrade head
alembic revision -m "New migration"
```

### "Can't locate revision identified by 'xyz'"

The migration file might have been deleted or the version in the database is incorrect. Check:

```bash
alembic history
alembic current
```

### "Database is already at revision xyz"

The migration has already been applied. This is informational and not an error.

### Foreign Key Constraint Violations

If you encounter foreign key errors during migration:
1. Check data integrity before migration
2. Consider temporarily disabling foreign keys in SQLite
3. Ensure migrations respect dependency order

## Integration with Existing Code

The Planted application currently initializes the database schema in code (via `PlantDatabase.init_database()` and `AuthService._init_users_table()`). When using migrations:

### First-Time Setup (New Installation)

For new installations, use migrations instead of the in-code schema initialization:

```bash
# Initialize new database with migrations
alembic upgrade head

# The application will detect existing schema and skip init
python3 main.py
```

### Existing Installations

For existing installations with data:

1. The database already has the schema
2. Mark it as migrated by stamping the initial migration:
   ```bash
   alembic stamp head
   ```
3. Future schema changes will use migrations

### Recommended Code Update

Consider adding a check in the initialization code to skip schema creation if Alembic is managing the database:

```python
# In plant_data.py and auth_service.py
def init_database(self):
    """Create database tables if they don't exist."""
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        
        # Check if Alembic is managing the database
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
        )
        if cursor.fetchone():
            # Alembic is managing this database, skip manual initialization
            return
        
        # Otherwise, create tables as before (backwards compatibility)
        # ... existing table creation code ...
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [SQLite ALTER TABLE Limitations](https://www.sqlite.org/lang_altertable.html)

## Support

For issues with migrations:
1. Check this documentation
2. Review Alembic logs for error details
3. Verify database backup exists
4. Create an issue on the GitHub repository with:
   - Migration command used
   - Full error message
   - Output of `alembic current` and `alembic history`
