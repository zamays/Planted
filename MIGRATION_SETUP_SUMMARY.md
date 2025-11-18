# Database Migration Setup Summary

This document provides a quick overview of the database migration system that has been implemented for the Planted application.

## What Was Implemented

The Planted application now has a complete database migration system using **Alembic** for version control of the SQLite database schema.

## Quick Reference

### Check Migration Status
```bash
alembic current
```

### Apply Migrations
```bash
# Backup first!
./scripts/backup_database.sh

# Then upgrade
alembic upgrade head
```

### Rollback Migration
```bash
alembic downgrade -1
```

### Create New Migration
```bash
alembic revision -m "Description of changes"
```

## Directory Structure

```
Planted/
├── alembic/                           # Migration system
│   ├── versions/                      # Migration scripts
│   │   └── e01efa1a265a_initial_schema.py
│   ├── env.py                        # Alembic environment
│   ├── script.py.mako                # Migration template
│   └── README                        # Quick reference
├── alembic.ini                       # Alembic configuration
├── scripts/
│   └── backup_database.sh            # Database backup script
└── docs/
    └── database_migrations.md        # Comprehensive guide
```

## Key Features

1. **Version Control**: Track schema changes through migration files
2. **Forward & Backward**: Upgrade and downgrade database schema
3. **Backup Script**: Automated database backup with `./scripts/backup_database.sh`
4. **Documentation**: Comprehensive guide in `docs/database_migrations.md`
5. **Minimal Changes**: No refactoring of existing database code required

## Initial Schema

The initial migration (`e01efa1a265a`) includes:
- ✅ `users` table - user accounts and authentication
- ✅ `plants` table - plant database with growing information
- ✅ `garden_plots` table - garden layout and plots
- ✅ `planted_items` table - what's planted where
- ✅ `care_tasks` table - automated care scheduling
- ✅ All performance indexes

## For New Installations

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database with migrations
alembic upgrade head

# Run the application
python3 main.py
```

## For Existing Installations

If you have an existing `garden.db` file from before migrations:

```bash
# Mark your existing database as up-to-date
alembic stamp head
```

This tells Alembic that your database already has the current schema.

## Before Any Migration

**Always backup first!**

```bash
./scripts/backup_database.sh
```

The script:
- Creates timestamped backups in `backups/` directory
- Keeps the last 10 backups automatically
- Shows backup size and details

## Documentation

For detailed information, see:
- **Full Guide**: [docs/database_migrations.md](docs/database_migrations.md)
- **Deployment**: [docs/deployment.md](docs/deployment.md)
- **Quick Ref**: [alembic/README](alembic/README)

## Common Workflows

### Making Schema Changes

1. Create a new migration:
   ```bash
   alembic revision -m "Add new field to plants table"
   ```

2. Edit the generated file in `alembic/versions/`

3. Implement `upgrade()` and `downgrade()` functions

4. Test on a backup:
   ```bash
   cp garden.db test.db
   # Edit alembic.ini to point to test.db
   alembic upgrade head
   # Verify changes
   sqlite3 test.db ".schema"
   ```

5. Apply to production:
   ```bash
   ./scripts/backup_database.sh
   alembic upgrade head
   ```

### Deploying Updates

```bash
# 1. Stop application
sudo systemctl stop planted  # or kill process

# 2. Backup database
./scripts/backup_database.sh

# 3. Pull latest code
git pull origin main

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run migrations
alembic upgrade head

# 6. Start application
sudo systemctl start planted  # or python3 main.py
```

## Troubleshooting

### "Can't locate revision"
```bash
alembic history
alembic current
```

### Migration fails
```bash
# Rollback
alembic downgrade -1

# Restore from backup
cp backups/garden.db.TIMESTAMP garden.db
```

### Database out of sync
```bash
# For existing database without migration history
alembic stamp head
```

## Integration with Existing Code

The application's database initialization code (`PlantDatabase.init_database()` and `AuthService._init_users_table()`) will continue to work for backwards compatibility. However, for new installations, using migrations is recommended:

1. **New Install**: Use `alembic upgrade head`
2. **Existing Install**: Use `alembic stamp head` once, then use migrations for future changes

## Support

- 📖 Full documentation: `docs/database_migrations.md`
- 🐛 Issues: GitHub Issues
- 📧 Questions: Create a GitHub Discussion

---

**Implementation Date**: November 18, 2024  
**Alembic Version**: 1.17.2  
**Initial Migration**: e01efa1a265a
