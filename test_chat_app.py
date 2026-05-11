#!/usr/bin/env python3
"""
Test script for the chat application.
Validates Sprint 1 acceptance criteria.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_data_loading():
    """Test that library data loads correctly."""
    print("Testing data loading...")
    data_path = Path(__file__).parent / "sample_data" / "library_of_things.json"

    try:
        with open(data_path, 'r') as f:
            data = json.load(f)

        assert "library_of_things" in data, "Missing library_of_things key"
        assert "items" in data["library_of_things"], "Missing items key"
        assert "categories" in data["library_of_things"], "Missing categories key"

        items = data["library_of_things"]["items"]
        categories = data["library_of_things"]["categories"]

        assert len(items) > 0, "No items in library data"
        assert len(categories) > 0, "No categories in library data"

        # Verify all items have required fields
        for item in items:
            assert "name" in item, f"Item missing name: {item}"
            assert "categories" in item, f"Item missing categories: {item}"
            assert "short_description" in item, f"Item missing short_description: {item}"

        print(f"✓ Data loading successful")
        print(f"  - {len(items)} items loaded")
        print(f"  - {len(categories)} categories found")
        return True

    except Exception as e:
        print(f"✗ Data loading failed: {e}")
        return False


def test_intent_detection():
    """Test keyword-based intent detection."""
    print("\nTesting intent detection...")

    from chat_app import IntentDetector, load_library_data

    data = load_library_data()
    categories = data.get("library_of_things", {}).get("categories", [])
    detector = IntentDetector(categories)

    test_cases = [
        # (message, expected_intent_type, expected_category)
        ("show me all games", "show_category", "Games"),
        ("Show me all TOOLS", "show_category", "Tools"),
        ("show all Chargers", "show_category", "Chargers"),
        ("how many games?", "count", "Games"),
        ("How many Tools?", "count", "Tools"),
        ("how many items in STEM Kits?", "count", "STEM Kits"),
        ("what's available?", "unknown", None),
    ]

    passed = 0
    for message, intent_type, expected_cat in test_cases:
        if intent_type == "show_category":
            result = detector.detect_show_category_intent(message)
            if result == expected_cat:
                print(f"✓ '{message}' → show {result}")
                passed += 1
            else:
                print(f"✗ '{message}' → expected {expected_cat}, got {result}")

        elif intent_type == "count":
            result = detector.detect_count_intent(message)
            if result == expected_cat:
                print(f"✓ '{message}' → count {result}")
                passed += 1
            else:
                print(f"✗ '{message}' → expected {expected_cat}, got {result}")

        elif intent_type == "unknown":
            show_result = detector.detect_show_category_intent(message)
            count_result = detector.detect_count_intent(message)
            if show_result is None and count_result is None:
                print(f"✓ '{message}' → no intent detected")
                passed += 1
            else:
                print(f"✗ '{message}' → unexpected intent detection")

    print(f"\n  {passed}/{len(test_cases)} intent detection tests passed")
    return passed == len(test_cases)


def test_item_filtering():
    """Test that items can be filtered by category."""
    print("\nTesting item filtering...")

    from chat_app import filter_items_by_category, load_library_data

    data = load_library_data()

    # Test filtering for each category
    categories = data.get("library_of_things", {}).get("categories", [])
    passed = 0

    for category in categories[:3]:  # Test first 3 categories
        items = filter_items_by_category(data, category)
        if len(items) > 0:
            print(f"✓ {category}: {len(items)} items found")
            passed += 1
        else:
            print(f"⚠ {category}: no items (may be empty category)")

    print(f"\n  {passed} categories tested")
    return passed > 0


def test_response_generation():
    """Test response generation for different intents."""
    print("\nTesting response generation...")

    from chat_app import generate_response, load_library_data, IntentDetector

    data = load_library_data()
    categories = data.get("library_of_things", {}).get("categories", [])
    detector = IntentDetector(categories)

    test_messages = [
        "show me all games",
        "how many tools?",
        "what do you have?",
    ]

    passed = 0
    for message in test_messages:
        try:
            response = generate_response(message, data, detector)
            if response and isinstance(response, str) and len(response) > 0:
                print(f"✓ Response generated for: '{message}'")
                print(f"  Length: {len(response)} chars")
                passed += 1
            else:
                print(f"✗ Invalid response for: '{message}'")
        except Exception as e:
            print(f"✗ Error generating response for '{message}': {e}")

    print(f"\n  {passed}/{len(test_messages)} responses generated successfully")
    return passed == len(test_messages)


def main():
    """Run all tests."""
    print("=" * 60)
    print("SPRINT 1 ACCEPTANCE CRITERIA VALIDATION")
    print("=" * 60)

    results = {
        "Data Loading": test_data_loading(),
        "Intent Detection": test_intent_detection(),
        "Item Filtering": test_item_filtering(),
        "Response Generation": test_response_generation(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    print("=" * 60)

    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
