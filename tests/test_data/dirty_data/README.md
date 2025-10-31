# Dirty Data Test Files

This directory contains test files with various types of invalid or problematic plant data. These files are designed to test the robustness of the plant import functionality in the Planted application.

## Test Files Overview

### 1. `missing_required_fields.json`
**Purpose:** Tests handling of missing required fields in plant data.

**Issues present:**
- Plant 1: Missing `scientific_name`, `planting_method`, `days_to_maturity`, and `care_notes`
- Plant 2: Missing entire `growing` section
- Plant 3: Missing `name` field (only has scientific_name)

**Expected behavior:**
- Should reject plants with missing critical fields
- Should provide clear error messages indicating which fields are missing
- Should not partially import incomplete plant data

---

### 2. `invalid_data_types.json`
**Purpose:** Tests handling of incorrect data types in various fields.

**Issues present:**
- Plant 1: String values for `days_to_germination` ("seven days") and `days_to_maturity` ("two months")
- Plant 2: Number for `scientific_name` (12345), string for `spacing_inches` ("twenty-four"), string for arrays (`companion_plants`, `avoid_plants`), string for `climate_zones`
- Plant 3: Number for `name` (999), number for `plant_type` (42), array for `season`, boolean values for `sun_requirements` and `water_needs`, null for `care_notes`

**Expected behavior:**
- Should validate data types before insertion
- Should reject plants with type mismatches
- Should provide clear error messages about expected vs. actual types

---

### 3. `malformed_json.json`
**Purpose:** Tests handling of syntactically invalid JSON.

**Issues present:**
- Missing comma after `scientific_name` on line 11 (between "scientific_name" and "plant_type")
- Invalid JSON syntax that cannot be parsed

**Expected behavior:**
- Should catch JSON parsing errors
- Should provide clear error message about malformed JSON
- Should not crash the application
- Should not corrupt existing data

---

### 4. `extra_unknown_fields.json`
**Purpose:** Tests handling of extra fields not defined in the schema.

**Extra fields included:**
- `version`, `metadata` at root level
- `id`, `common_names`, `origin`, `price`, `supplier` in plant objects
- `optimal_temperature`, `frost_tolerance` in growing section
- `fertilizer_type`, `ph_range` in care section
- `pollination` in compatibility section
- Entire `harvest` section with `method`, `storage_days`, `best_time`
- Entire `nutritional_info` section with `calories`, `vitamins`
- `photo_url`, `tags` in plant 2

**Expected behavior:**
- Should gracefully ignore unknown fields
- Should successfully import valid required fields
- Should not fail due to presence of extra data

---

### 5. `null_empty_values.json`
**Purpose:** Tests handling of null and empty string values.

**Issues present:**
- Plant 1: Empty string for `name`
- Plant 2: `null` for `name`, `care_notes`, `avoid_plants`, and `climate_zones`
- Plant 3: Empty strings for most fields, `null` for numeric fields

**Expected behavior:**
- Should reject plants with null or empty required fields
- Should handle nullable optional fields appropriately
- Should distinguish between empty strings and null values
- Should provide validation errors for empty required fields

---

### 6. `out_of_range_values.json`
**Purpose:** Tests handling of values outside reasonable ranges.

**Issues present:**
- Plant 1: Negative values for `days_to_germination` (-5), `days_to_maturity` (-30), `spacing_inches` (-10)
- Plant 2: Extremely large values for days (99999, 999999) and spacing (10000), invalid climate zones (14, 15, 20, 99)
- Plant 3: Zero values for all numeric fields
- Plant 4: Invalid season ("monsoon"), invalid planting method ("teleportation"), invalid sun requirements ("total_darkness"), invalid water needs ("never"), negative and invalid climate zones (-5, 0, 100)

**Expected behavior:**
- Should validate numeric ranges (e.g., days > 0, spacing > 0)
- Should validate enumerated values (season, planting_method, sun_requirements, water_needs)
- Should validate climate zones (typically 1-13 for USDA zones)
- Should reject plants with invalid values
- Should provide clear validation error messages

---

### 7. `duplicate_entries.json`
**Purpose:** Tests handling of duplicate plant entries.

**Issues present:**
- Two plants named "Lettuce" with different data
- Three plants named "Tomato" (two identical, one slightly different)
- Tests both exact duplicates and plants with same name but different properties

**Expected behavior:**
- Should detect duplicate names
- Should either:
  - Reject duplicates with an error, or
  - Update existing entries, or
  - Allow duplicates with different IDs (depends on business logic)
- Should document which behavior is intended
- Should not create duplicate database entries unintentionally

---

### 8. `mixed_valid_invalid.json`
**Purpose:** Tests handling of files containing both valid and invalid plant entries.

**Contents:**
- Plant 1 (Valid): Complete and correct "Lettuce" entry
- Plant 2 (Invalid): "Tomato" with multiple type errors (numeric scientific_name, string days_to_germination, string for array companion_plants, null care_notes)
- Plant 3 (Valid): Complete and correct "Spinach" entry
- Plant 4 (Invalid): Empty string for `name` field
- Plant 5 (Valid): Complete and correct "Basil" entry

**Expected behavior:**
- Should attempt to process all plants in the file
- Should successfully import valid plants (1, 3, 5)
- Should reject invalid plants (2, 4) with appropriate errors
- Should not stop processing after encountering an error
- Should report which plants succeeded and which failed
- Should maintain transaction integrity (all-or-nothing import, or partial import with clear reporting)

---

### 9. `special_characters.json`
**Purpose:** Tests handling of special characters, Unicode, and potential injection attacks.

**Issues present:**
- Plant 1: Emoji characters (🌶️, 🔥) in name and care notes
- Plant 2: Newline characters (\n), tab characters (\t), carriage returns (\r\n) in various fields
- Plant 3: Mixed quote types (single quotes, double quotes) in names and care notes
- Plant 4: Accented and non-ASCII Latin characters (ü, ñ, é, ç) - legitimate international characters
- Plant 5: Asian characters (Chinese, Japanese, Korean) in names and descriptions
- Plant 6: Mathematical and typographic symbols (©, ®, ™, ±, ×, etc.)
- Plant 7: SQL injection attempts and XSS (Cross-Site Scripting) patterns

**Expected behavior:**
- Should properly handle UTF-8 encoding for international characters
- Should sanitize or escape special characters appropriately
- Should prevent SQL injection attacks through parameterized queries
- Should handle or strip emoji characters based on application requirements
- Should normalize whitespace characters (newlines, tabs, carriage returns)
- Should escape HTML/JavaScript in display contexts to prevent XSS
- Should maintain data integrity while handling special characters
- Should not crash or corrupt data when encountering unusual characters

**Security considerations:**
- SQL injection: The application should use parameterized queries (which it does via sqlite3)
- XSS prevention: Should escape HTML/JavaScript when displaying in web interface
- Unicode handling: Should properly encode/decode UTF-8 characters
- Input sanitization: Should validate and sanitize input appropriately

---

## Usage

These test files can be used to:

1. **Unit Testing:** Test individual import functions with various invalid inputs
2. **Integration Testing:** Test the complete import workflow with bad data
3. **Error Handling Validation:** Verify that appropriate errors are raised
4. **Data Validation Testing:** Ensure validation logic catches all problematic data
5. **Robustness Testing:** Confirm the application doesn't crash with bad input

## Testing Recommendations

When using these files:

1. Test that the import process fails gracefully (no crashes)
2. Verify appropriate error messages are generated
3. Ensure database integrity is maintained (no partial imports)
4. Check that valid plants aren't affected by invalid ones in the same file
5. Confirm that the application continues to function after encountering bad data

## Real-World Scenarios

These test cases represent real-world scenarios such as:
- **Missing fields:** User-exported data with incomplete information
- **Type errors:** Data from CSV conversions or manual JSON editing
- **Malformed JSON:** Corrupted files or manual editing mistakes
- **Extra fields:** Data exported from other systems with different schemas
- **Null values:** Database exports with NULL values not handled properly
- **Out-of-range values:** Data entry errors or calculation mistakes
- **Duplicates:** Multiple imports or merged datasets

## Notes

- These files intentionally contain errors and should NOT be used for actual plant data
- The valid plant data structure can be found in `garden_manager/database/seeds/default_plants.json`
- Each test file can be used independently or as part of a comprehensive test suite
