# Test Data Files Summary

## Overview

This directory contains **9 comprehensive test data files** designed to test the robustness of the plant import functionality in the Planted application. These files simulate various types of problematic data that might be encountered when importing plant information.

## Quick Reference

| File Name | Purpose | Plant Count | Key Issues |
|-----------|---------|-------------|------------|
| `missing_required_fields.json` | Missing required fields | 3 | Missing name, scientific_name, planting_method, etc. |
| `invalid_data_types.json` | Wrong data types | 3 | Strings for numbers, numbers for strings, wrong types everywhere |
| `malformed_json.json` | Syntax errors | 2 | Missing comma - will not parse |
| `extra_unknown_fields.json` | Extra/unknown fields | 2 | Additional fields not in schema |
| `null_empty_values.json` | Null and empty values | 3 | Empty strings and null values |
| `out_of_range_values.json` | Invalid ranges | 4 | Negative numbers, extreme values, invalid enums |
| `duplicate_entries.json` | Duplicate plants | 5 | Multiple plants with same name |
| `mixed_valid_invalid.json` | Mix of good/bad data | 5 | 3 valid, 2 invalid plants |
| `special_characters.json` | Special characters | 7 | Unicode, emoji, SQL injection patterns |

## Testing Categories

### 1. Data Completeness
- **File:** `missing_required_fields.json`
- **Tests:** Missing required fields at various levels

### 2. Data Type Validation
- **File:** `invalid_data_types.json`
- **Tests:** Type mismatches (string vs number, etc.)

### 3. JSON Syntax
- **File:** `malformed_json.json`
- **Tests:** Syntactically invalid JSON

### 4. Schema Flexibility
- **File:** `extra_unknown_fields.json`
- **Tests:** Additional fields beyond schema

### 5. Null Handling
- **File:** `null_empty_values.json`
- **Tests:** Null values and empty strings

### 6. Range Validation
- **File:** `out_of_range_values.json`
- **Tests:** Out-of-range numbers, invalid enums

### 7. Uniqueness
- **File:** `duplicate_entries.json`
- **Tests:** Duplicate plant entries

### 8. Partial Import
- **File:** `mixed_valid_invalid.json`
- **Tests:** Mix of valid and invalid data

### 9. Character Encoding
- **File:** `special_characters.json`
- **Tests:** Unicode, emoji, injection attempts

## How to Use

### Quick Demo
Run the demo script to see the test files in action:
```bash
python3 tests/test_dirty_data_demo.py
```

### In Unit Tests
```python
import json
from garden_manager.database.plant_data import PlantDatabase

def test_invalid_data_handling():
    with open('tests/test_data/dirty_data/invalid_data_types.json') as f:
        data = json.load(f)
    
    # Test that invalid data is rejected
    # ... your test code here
```

### Manual Testing
```bash
# Try to parse each file
python3 -c "import json; print(json.load(open('tests/test_data/dirty_data/missing_required_fields.json')))"
```

## Expected Behaviors

The import system should:

1. ✅ **Validate data types** before insertion
2. ✅ **Check required fields** are present
3. ✅ **Handle malformed JSON** gracefully
4. ✅ **Ignore unknown fields** (forward compatibility)
5. ✅ **Reject null/empty required fields**
6. ✅ **Validate value ranges** (days > 0, valid seasons, etc.)
7. ✅ **Handle duplicates** according to business logic
8. ✅ **Support partial imports** or fail atomically
9. ✅ **Sanitize special characters** (prevent SQL injection, XSS)

## Documentation

See `tests/test_data/dirty_data/README.md` for detailed documentation of each test file, including:
- Specific issues in each plant entry
- Expected application behavior
- Real-world scenarios represented
- Security considerations

## Demo Output

The demo script (`test_dirty_data_demo.py`) provides:
- ✅ Verification that malformed JSON is rejected
- ✅ Confirmation that valid JSON (with invalid data) can be parsed
- ✅ Analysis of missing fields in test data
- ✅ Detection of special characters and potential injection patterns

## Integration with CI/CD

These test files can be used in automated testing:

```yaml
# Example GitHub Actions workflow
- name: Test data validation
  run: |
    python3 tests/test_dirty_data_demo.py
    python3 -m pytest tests/unit/test_import_validation.py
```

## Contributing

When adding new test scenarios:
1. Create a new JSON file in this directory
2. Document the issues in the README.md
3. Add a test case to the demo script
4. Update this summary

## Notes

- These files are for **testing only** - do not use for actual plant data
- The reference for valid data structure is in `garden_manager/database/seeds/default_plants.json`
- All test files (except `malformed_json.json`) are syntactically valid JSON but contain semantic errors

## File Statistics

- **Total test files:** 9
- **Total test plant entries:** 35
- **Lines of test data:** ~400
- **Lines of documentation:** ~500
- **Coverage:** All major error categories

---

**Created:** 2025-10-31  
**Purpose:** Test plant import robustness  
**Status:** Ready for use ✅
