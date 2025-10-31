#!/usr/bin/env python3
"""
Test script demonstrating how to use dirty data test files to validate
the plant import functionality.

This script tests the robustness of the plant data loader against various
types of invalid or problematic data.
"""

import sys
import json
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_malformed_json():
    """Test handling of syntactically invalid JSON."""
    print_header("Test 1: Malformed JSON")
    
    file_path = "tests/test_data/dirty_data/malformed_json.json"
    print(f"Testing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("❌ UNEXPECTED: Malformed JSON was parsed successfully!")
        print("   The file should contain syntax errors.")
        return False
    except json.JSONDecodeError as e:
        print(f"✅ EXPECTED: JSON parsing failed with error:")
        print(f"   {e}")
        return True
    except Exception as e:
        print(f"⚠️  UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False


def test_valid_json_parsing():
    """Test that valid test files can be parsed."""
    print_header("Test 2: Valid JSON Parsing (with invalid data)")
    
    test_files = [
        "missing_required_fields.json",
        "invalid_data_types.json",
        "extra_unknown_fields.json",
        "null_empty_values.json",
        "out_of_range_values.json",
        "duplicate_entries.json",
        "mixed_valid_invalid.json",
        "special_characters.json"
    ]
    
    results = []
    for filename in test_files:
        file_path = f"tests/test_data/dirty_data/{filename}"
        print(f"\nTesting: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verify basic structure
            if "plants" not in data:
                print(f"   ⚠️  WARNING: No 'plants' key found")
                results.append(False)
            else:
                plant_count = len(data.get("plants", []))
                print(f"   ✅ JSON parsed successfully: {plant_count} plants")
                results.append(True)
                
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON parsing failed: {e}")
            results.append(False)
        except Exception as e:
            print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    print(f"\n   Summary: {success_count}/{total_count} files parsed successfully")
    return all(results)


def test_data_structure_analysis():
    """Analyze the structure of test data files."""
    print_header("Test 3: Data Structure Analysis")
    
    file_path = "tests/test_data/dirty_data/missing_required_fields.json"
    print(f"Analyzing: {file_path}\n")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, plant in enumerate(data.get("plants", []), 1):
            print(f"Plant {i}: {plant.get('name', '[NO NAME]')}")
            
            # Check for required fields
            required_fields = ["name", "scientific_name", "plant_type", "growing", "care", "compatibility"]
            missing_fields = [field for field in required_fields if field not in plant]
            
            if missing_fields:
                print(f"   ⚠️  Missing required fields: {', '.join(missing_fields)}")
            
            # Check growing info
            if "growing" in plant:
                growing_required = ["season", "planting_method", "days_to_germination", 
                                   "days_to_maturity", "spacing_inches"]
                growing_missing = [field for field in growing_required 
                                  if field not in plant["growing"]]
                if growing_missing:
                    print(f"   ⚠️  Missing growing fields: {', '.join(growing_missing)}")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {type(e).__name__}: {e}")
        return False


def test_special_characters():
    """Test handling of special characters and Unicode."""
    print_header("Test 4: Special Characters & Unicode")
    
    file_path = "tests/test_data/dirty_data/special_characters.json"
    print(f"Testing: {file_path}\n")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for i, plant in enumerate(data.get("plants", []), 1):
            name = plant.get("name", "[NO NAME]")
            print(f"Plant {i}: {name}")
            
            # Check for various special character types
            has_emoji = any(ord(c) > 127000 for c in name)
            has_unicode = any(ord(c) > 127 and ord(c) < 127000 for c in name)
            has_injection = any(pattern in name.lower() 
                              for pattern in ["sql", "drop", "script", "alert"])
            
            if has_emoji:
                print(f"   📱 Contains emoji characters")
            if has_unicode:
                print(f"   🌐 Contains Unicode characters")
            if has_injection:
                print(f"   ⚠️  Contains potential injection patterns")
            
        print("\n✅ All plants with special characters parsed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


def main():
    """Run all tests."""
    print_header("Dirty Data Test Suite")
    print("Testing plant import data validation with problematic data.\n")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}\n")
    
    results = {
        "Malformed JSON": test_malformed_json(),
        "Valid JSON Parsing": test_valid_json_parsing(),
        "Data Structure Analysis": test_data_structure_analysis(),
        "Special Characters": test_special_characters(),
    }
    
    # Print summary
    print_header("Test Summary")
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The dirty data files are ready for use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
