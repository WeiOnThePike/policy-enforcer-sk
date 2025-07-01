#!/usr/bin/env python3
"""
Unit tests to verify the case sensitivity fix works correctly.
"""

import sys
import os
import unittest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from policy_enforcer.state import get_state, reset_state, Activity
from policy_enforcer.rules import get_rule_engine
from policy_enforcer.items import Item, ItemRequirements
from policy_enforcer.tools import get_plugins


class TestCaseSensitivityFix(unittest.TestCase):
    """Test case sensitivity fix for item handling."""
    
    def setUp(self):
        """Set up test environment."""
        reset_state()
        self.state = get_state()
        self.rule_engine = get_rule_engine()
        self.plugins = get_plugins()
        
        # Get shopping plugin
        self.shopping_plugin = None
        for plugin in self.plugins:
            if hasattr(plugin, 'shopping'):
                self.shopping_plugin = plugin
                break
        
        # Get activity plugin  
        self.activity_plugin = None
        for plugin in self.plugins:
            if hasattr(plugin, 'choose_activity'):
                self.activity_plugin = plugin
                break
    
    def test_item_validation_case_insensitive(self):
        """Test that item validation is now case-insensitive."""
        # All these should be valid now
        test_cases = [
            ("TV", True),
            ("tv", True),
            ("Tv", True),
            ("tV", True),
            ("Xbox", True),
            ("xbox", True),
            ("XBOX", True),
            ("xBoX", True),
            ("Hiking Boots", True),
            ("hiking boots", True),
            ("HIKING BOOTS", True),
            ("HiKiNg BoOtS", True),
            ("Goggles", True),
            ("goggles", True),
            ("GOGGLES", True),
            ("InvalidItem", False),
            ("invalid", False),
            ("", False),
        ]
        
        for item_name, expected in test_cases:
            with self.subTest(item=item_name):
                result = ItemRequirements.is_valid_item(item_name)
                self.assertEqual(result, expected, f"ItemRequirements.is_valid_item('{item_name}') should return {expected}")
        
        print("✅ Item validation is case-insensitive")
    
    def test_item_name_normalization(self):
        """Test that item names are normalized to correct case."""
        test_cases = [
            ("tv", "TV"),
            ("TV", "TV"),
            ("Tv", "TV"),
            ("tV", "TV"),
            ("xbox", "Xbox"),
            ("Xbox", "Xbox"),
            ("XBOX", "Xbox"),
            ("xBoX", "Xbox"),
            ("hiking boots", "Hiking Boots"),
            ("Hiking Boots", "Hiking Boots"),
            ("HIKING BOOTS", "Hiking Boots"),
            ("HiKiNg BoOtS", "Hiking Boots"),
            ("goggles", "Goggles"),
            ("Goggles", "Goggles"),
            ("GOGGLES", "Goggles"),
        ]
        
        for input_name, expected_output in test_cases:
            with self.subTest(input=input_name):
                result = ItemRequirements.normalize_item_name(input_name)
                self.assertEqual(result, expected_output, f"normalize_item_name('{input_name}') should return '{expected_output}'")
        
        print("✅ Item name normalization works correctly")
    
    def test_inventory_normalization(self):
        """Test that items are normalized when added to inventory."""
        # Add items with various cases
        self.state.add_to_inventory("tv")
        self.state.add_to_inventory("XBOX")
        self.state.add_to_inventory("hiking boots")
        self.state.add_to_inventory("GOGGLES")
        
        # Check that they're normalized in inventory
        expected_inventory = {"TV", "Xbox", "Hiking Boots", "Goggles"}
        self.assertEqual(self.state.inventory, expected_inventory)
        print("✅ Inventory normalization works correctly")
    
    def test_shopping_plugin_case_insensitive(self):
        """Test that shopping plugin works with any case."""
        # Buy items with different cases
        result1 = self.shopping_plugin.shopping("tv")
        self.assertIn("Successfully purchased", result1)
        self.assertIn("TV", self.state.inventory)
        
        result2 = self.shopping_plugin.shopping("XBOX")
        self.assertIn("Successfully purchased", result2)
        self.assertIn("Xbox", self.state.inventory)
        
        # Verify normalized names in inventory
        self.assertIn("TV", self.state.inventory)
        self.assertIn("Xbox", self.state.inventory)
        self.assertNotIn("tv", self.state.inventory)
        self.assertNotIn("XBOX", self.state.inventory)
        
        print("✅ Shopping plugin normalizes item cases")
    
    def test_gaming_rules_with_case_insensitive_items(self):
        """Test that gaming rules work with case-insensitive item purchases."""
        # Buy gaming items with wrong case
        result1 = self.shopping_plugin.shopping("tv")
        self.assertIn("Successfully purchased", result1)
        
        result2 = self.shopping_plugin.shopping("xbox")
        self.assertIn("Successfully purchased", result2)
        
        # Try to play games - should work now
        result = self.activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        self.assertNotIn("Rule violation", result)
        self.assertIn("chosen", result.lower())
        
        # Verify state
        self.assertEqual(self.state.chosen_activity, Activity.PLAY_GAMES)
        self.assertIn("TV", self.state.inventory)
        self.assertIn("Xbox", self.state.inventory)
        
        print("✅ Gaming rules work with case-insensitive purchases")
    
    def test_rule_engine_with_mixed_case_inventory(self):
        """Test rule engine with mixed case items."""
        # Manually add items with various cases (simulating old data)
        self.state.inventory.add("tv")  # Wrong case
        self.state.inventory.add("Xbox")  # Correct case
        
        # Rule should NOW work because of case-insensitive comparison
        result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
        self.assertTrue(result.allowed, "Should work with mixed case items due to case-insensitive comparison")
        
        # Test with only one item in wrong case
        reset_state()
        self.state = get_state()
        self.state.inventory.add("tv")  # Only TV in wrong case
        
        result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
        self.assertFalse(result.allowed, "Should fail when missing Xbox (regardless of case)")
        self.assertIn("Xbox", result.reason, "Should mention missing Xbox")
        
        print("✅ Rule engine works correctly with mixed case items")
    
    def test_missing_items_detection_case_insensitive(self):
        """Test that missing items detection is case-insensitive."""
        # Add items with wrong case
        inventory = {"tv", "hiking boots"}
        
        # Should detect Xbox as missing for gaming
        missing = ItemRequirements.get_missing_items(Activity.PLAY_GAMES.value, inventory)
        missing_names = [item.value for item in missing]
        self.assertEqual(missing_names, ["Xbox"], "Should detect Xbox as missing")
        
        # Should detect nothing missing for camping
        missing = ItemRequirements.get_missing_items(Activity.GO_CAMPING.value, inventory)
        self.assertEqual(len(missing), 0, "Should detect no missing items for camping")
        
        print("✅ Missing items detection is case-insensitive")


def run_case_sensitivity_tests():
    """Run all case sensitivity tests."""
    print("🚀 Testing Case Sensitivity Fix...\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestCaseSensitivityFix))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n🎉 All case sensitivity tests passed!")
        print("✅ Case sensitivity bug has been fixed:")
        print("   • Item validation is now case-insensitive")
        print("   • Item names are normalized when added to inventory")
        print("   • Shopping plugin accepts any case")
        print("   • Gaming rules work with case-insensitive purchases")
        print("   • Missing items detection is case-insensitive")
        return True
    else:
        print(f"\n❌ Case sensitivity tests failed!")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        return False


if __name__ == "__main__":
    success = run_case_sensitivity_tests()
    sys.exit(0 if success else 1)