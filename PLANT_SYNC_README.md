# Plant Database Auto-Sync Feature

## Overview

The Planted application now automatically syncs plant data from the JSON seed file to the SQLite database on every app startup. This makes it easy to add new plants or update existing ones without manual database manipulation.

## How It Works

### On First Launch
- Reads all plants from `garden_manager/database/seeds/default_plants.json`
- Loads all 90+ default plants into the database
- Marks them with `is_custom = FALSE`

### On Subsequent Launches
- Compares JSON data with existing database plants
- **Updates** existing default plants with any changes
- **Adds** new plants found in the JSON
- **Preserves** custom plants (never touches `is_custom = TRUE` plants)
- **Prevents** duplicate entries

## Usage

### Adding a New Plant

1. Edit `garden_manager/database/seeds/default_plants.json`
2. Add your plant following the JSON structure:
   ```json
   {
     "name": "New Plant",
     "scientific_name": "Plantus newus",
     "plant_type": "vegetable",
     "growing": {
       "season": "spring",
       "planting_method": "seed",
       "days_to_germination": 7,
       "days_to_maturity": 60,
       "spacing_inches": 12
     },
     "care": {
       "sun_requirements": "full_sun",
       "water_needs": "medium",
       "care_notes": "Care instructions"
     },
     "compatibility": {
       "companion_plants": ["tomatoes"],
       "avoid_plants": ["fennel"],
       "climate_zones": [5, 6, 7, 8]
     }
   }
   ```
3. Restart the app - the new plant is automatically added!

### Updating an Existing Plant

1. Find the plant by name in `default_plants.json`
2. Modify any fields (e.g., care notes, days to maturity, etc.)
3. Save the file
4. Restart the app - changes are automatically synced!

### Testing the Sync

Run the included test script:
```bash
python3 test_plant_sync.py
```

This will:
- Create a fresh database
- Test initial loading
- Test sync on restart (no duplicates)
- Test change detection
- Verify the feature is working correctly

## Technical Details

### Modified Files

**`garden_manager/database/plant_data.py`**
- Updated `populate_plant_data()` method
- Added logic to detect and sync changes
- Distinguishes between initial load and sync mode

### Database Schema

Plants table includes `is_custom` flag:
- `FALSE` or `NULL`: Default plants (will be synced)
- `TRUE`: Custom plants (never modified by sync)

### Sync Logic

```python
if existing_count == 0:
    # First run - load all plants
    insert_all_plants()
else:
    # Sync mode - update existing, add new
    for plant in json_plants:
        if exists_in_db(plant.name):
            update_plant(plant)  # Only non-custom plants
        else:
            insert_plant(plant)
```

### Safety Features

1. **Custom Plant Protection**: Plants added via web interface are marked `is_custom = TRUE` and are never modified by sync
2. **No Deletion**: Removing a plant from JSON doesn't delete it from the database
3. **Idempotent**: Running sync multiple times produces the same result
4. **Transaction-Safe**: All changes committed together

## Output Messages

When the app starts, you'll see:

**First Run:**
```
🔧 Initializing services...
   ✅ Loaded 90 default plants into database
   ✅ Database services initialized
```

**Subsequent Runs:**
```
🔧 Initializing services...
   ✅ Plant sync: 0 added, 90 updated
   ✅ Database services initialized
```

**When Changes Detected:**
```
🔧 Initializing services...
   ✅ Plant sync: 2 added, 90 updated
   ✅ Database services initialized
```

## Benefits

1. **Easy Maintenance**: No need to manually update the database
2. **Version Control Friendly**: Plant data lives in a JSON file that can be tracked in git
3. **Safe**: Custom user-added plants are protected
4. **Automatic**: No user intervention required
5. **Efficient**: Only updates what's changed

## Future Enhancements

Potential improvements:
- Sync on file change detection (without restart)
- Backup database before sync
- Sync conflict resolution UI
- Import/export plant collections
- Community plant sharing

## Examples

### Example 1: Adding a Seasonal Variety

Want to add "Cherry Tomatoes" as a variation?

1. Copy an existing tomato entry in `default_plants.json`
2. Change the name to "Cherry Tomatoes"
3. Adjust `days_to_maturity` to 60 (faster than regular tomatoes)
4. Update care notes
5. Restart the app - new variety available!

### Example 2: Updating Growing Information

Found better care instructions for lettuce?

1. Find "Lettuce" in `default_plants.json`
2. Update the `care_notes` field
3. Restart the app - all users see the improved information!

### Example 3: Expanding Climate Zones

Want to add more zones for a hardy plant?

1. Find the plant in `default_plants.json`
2. Expand the `climate_zones` array: `[3, 4, 5, 6, 7, 8, 9, 10]`
3. Restart the app - plant now available in more locations!

## Troubleshooting

### Sync Not Working?

Check that:
- JSON file is valid (use a JSON validator)
- File path is correct: `garden_manager/database/seeds/default_plants.json`
- Plant names match exactly (case-sensitive)
- Database file has write permissions

### Custom Plants Being Modified?

- Verify the plant has `is_custom = TRUE` in the database
- Custom plants added via `/plants/add` should automatically be marked
- Check with: `SELECT name, is_custom FROM plants WHERE name = 'Your Plant';`

### Changes Not Appearing?

- Ensure you saved the JSON file
- Completely restart the application (not just refresh browser)
- Check console output for sync messages
- Run `python3 test_plant_sync.py` to verify

## Contact

For issues or questions about this feature, see the main [CLAUDE.md](CLAUDE.md) documentation.