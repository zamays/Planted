#!/bin/bash
# Database backup script for Planted
# Creates timestamped backups and maintains only the 10 most recent backups

# Configuration
DB_FILE="garden.db"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_FILE}.${TIMESTAMP}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if database file exists
if [ ! -f "${DB_FILE}" ]; then
    echo "Error: Database file ${DB_FILE} not found!"
    exit 1
fi

# Create backup
echo "Creating backup: ${BACKUP_FILE}"
cp "${DB_FILE}" "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "✓ Backup created successfully"
    
    # Keep only last 10 backups
    BACKUP_COUNT=$(ls -t "${BACKUP_DIR}/${DB_FILE}."* 2>/dev/null | wc -l)
    if [ "${BACKUP_COUNT}" -gt 10 ]; then
        echo "Cleaning up old backups (keeping last 10)..."
        ls -t "${BACKUP_DIR}/${DB_FILE}."* | tail -n +11 | xargs -r rm
        echo "✓ Old backups cleaned up"
    fi
    
    # Display backup info
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo ""
    echo "Backup Details:"
    echo "  File: ${BACKUP_FILE}"
    echo "  Size: ${BACKUP_SIZE}"
    echo "  Total backups: $(ls -t "${BACKUP_DIR}/${DB_FILE}."* 2>/dev/null | wc -l)"
    
    exit 0
else
    echo "✗ Backup failed!"
    exit 1
fi
