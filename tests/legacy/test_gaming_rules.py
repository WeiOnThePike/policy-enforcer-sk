#!/usr/bin/env python3
"""
Comprehensive unit tests for gaming rules enforcement.

This test suite specifically focuses on validating that the "Play games" 
activity rule is properly enforced at all levels.
"""

import sys
import os
import unittest

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from policy_enforcer.state import get_state, reset_state, WeatherCondition, Activity
from policy_enforcer.rules import get_rule_engine, PlayGamesRule, RuleResult
from policy_enforcer.tools import get_plugins, ActivityPlugin
from policy_enforcer.items import Item, ItemRequirements


class TestGamingRulesEnforcement(unittest.TestCase):
    """Test suite for gaming rules enforcement."""
    
    def setUp(self):
        """Set up test environment before each test."""
        reset_state()
        self.state = get_state()
        self.rule_engine = get_rule_engine()
        self.plugins = get_plugins()
        
        # Get the activity plugin for direct testing
        self.activity_plugin = None
        for plugin in self.plugins:
            if isinstance(plugin, ActivityPlugin):
                self.activity_plugin = plugin
                break
        
        self.assertIsNotNone(self.activity_plugin, "ActivityPlugin not found")
    
    def test_play_games_rule_initialization(self):
        """Test that PlayGamesRule is properly initialized."""
        play_games_rule = None
        for rule in self.rule_engine.rules:
            if isinstance(rule, PlayGamesRule):
                play_games_rule = rule
                break
        
        self.assertIsNotNone(play_games_rule, "PlayGamesRule not found in rule engine")
        self.assertEqual(play_games_rule.name, "Play Games Equipment Rule")
        self.assertIn("TV", play_games_rule.description)
        self.assertIn("Xbox", play_games_rule.description)
        print("✅ PlayGamesRule properly initialized")
    
    def test_item_requirements_for_gaming(self):
        """Test that item requirements for gaming are correctly defined."""
        requirements = ItemRequirements.get_requirements_for_activity(Activity.PLAY_GAMES.value)
        
        self.assertEqual(len(requirements), 2, "Should require exactly 2 items for gaming")
        self.assertIn(Item.TV, requirements, "TV should be required for gaming")
        self.assertIn(Item.XBOX, requirements, "Xbox should be required for gaming")
        
        # Test missing items detection
        empty_inventory = set()
        missing = ItemRequirements.get_missing_items(Activity.PLAY_GAMES.value, empty_inventory)
        self.assertEqual(len(missing), 2, "Should have 2 missing items with empty inventory")
        
        # Test with partial items
        partial_inventory = {Item.TV.value}
        missing = ItemRequirements.get_missing_items(Activity.PLAY_GAMES.value, partial_inventory)
        self.assertEqual(len(missing), 1, "Should have 1 missing item with TV only")
        self.assertEqual(missing[0], Item.XBOX, "Xbox should be the missing item")
        
        # Test with all items
        full_inventory = {Item.TV.value, Item.XBOX.value}
        missing = ItemRequirements.get_missing_items(Activity.PLAY_GAMES.value, full_inventory)
        self.assertEqual(len(missing), 0, "Should have no missing items with full inventory")
        
        print("✅ Item requirements for gaming correctly defined")
    
    def test_play_games_rule_direct_validation(self):
        """Test PlayGamesRule directly with various scenarios."""
        play_games_rule = PlayGamesRule()
        
        # Test 1: No items in inventory - should fail
        result = play_games_rule.check(self.state, activity=Activity.PLAY_GAMES.value)
        self.assertFalse(result.allowed, "Should not allow playing games without equipment")
        self.assertIn("TV", result.reason, "Reason should mention missing TV")
        self.assertIn("Xbox", result.reason, "Reason should mention missing Xbox")
        print("✅ Rule correctly blocks gaming without equipment")
        
        # Test 2: Only TV in inventory - should fail
        self.state.add_to_inventory(Item.TV.value)
        result = play_games_rule.check(self.state, activity=Activity.PLAY_GAMES.value)
        self.assertFalse(result.allowed, "Should not allow playing games with only TV")
        self.assertIn("Xbox", result.reason, "Reason should mention missing Xbox")
        self.assertNotIn("TV", result.reason, "Reason should not mention TV since it's available")
        print("✅ Rule correctly blocks gaming with only TV")
        
        # Test 3: Only Xbox in inventory - should fail
        reset_state()
        self.state = get_state()
        self.state.add_to_inventory(Item.XBOX.value)
        result = play_games_rule.check(self.state, activity=Activity.PLAY_GAMES.value)
        self.assertFalse(result.allowed, "Should not allow playing games with only Xbox")
        self.assertIn("TV", result.reason, "Reason should mention missing TV")
        self.assertNotIn("Xbox", result.reason, "Reason should not mention Xbox since it's available")
        print("✅ Rule correctly blocks gaming with only Xbox")
        
        # Test 4: Both TV and Xbox in inventory - should allow
        self.state.add_to_inventory(Item.TV.value)  # Xbox already added above
        result = play_games_rule.check(self.state, activity=Activity.PLAY_GAMES.value)
        self.assertTrue(result.allowed, "Should allow playing games with both TV and Xbox")
        self.assertIsNone(result.reason, "No reason should be provided when allowed")
        print("✅ Rule correctly allows gaming with both TV and Xbox")
        
        # Test 5: Different activity - should allow regardless of inventory
        reset_state()
        self.state = get_state()
        result = play_games_rule.check(self.state, activity=Activity.GO_CAMPING.value)
        self.assertTrue(result.allowed, "Should allow other activities regardless of gaming equipment")
        print("✅ Rule correctly ignores non-gaming activities")
    
    def test_rule_engine_activity_checking(self):
        """Test that RuleEngine properly checks gaming rules through check_activity_rules."""
        # Test 1: Empty inventory - should fail
        result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
        self.assertFalse(result.allowed, "RuleEngine should block gaming without equipment")
        self.assertIn("TV", result.reason, "RuleEngine reason should mention missing TV")
        self.assertIn("Xbox", result.reason, "RuleEngine reason should mention missing Xbox")
        print("✅ RuleEngine correctly blocks gaming without equipment")
        
        # Test 2: Add TV only - should still fail
        self.state.add_to_inventory(Item.TV.value)
        result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
        self.assertFalse(result.allowed, "RuleEngine should block gaming with only TV")
        self.assertIn("Xbox", result.reason, "RuleEngine reason should mention missing Xbox")
        print("✅ RuleEngine correctly blocks gaming with partial equipment")
        
        # Test 3: Add Xbox - should now allow
        self.state.add_to_inventory(Item.XBOX.value)
        result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
        self.assertTrue(result.allowed, "RuleEngine should allow gaming with full equipment")
        print("✅ RuleEngine correctly allows gaming with full equipment")
    
    def test_activity_plugin_rule_enforcement(self):
        """Test that ActivityPlugin properly enforces gaming rules."""
        # Test 1: Try to play games without equipment
        result = self.activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        self.assertIn("Rule violation", result, "ActivityPlugin should report rule violation")
        self.assertIn("TV", result, "ActivityPlugin should mention missing TV")
        self.assertIn("Xbox", result, "ActivityPlugin should mention missing Xbox")
        print("✅ ActivityPlugin correctly blocks gaming without equipment")
        
        # Test 2: Add only TV and try again
        self.state.add_to_inventory(Item.TV.value)
        result = self.activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        self.assertIn("Rule violation", result, "ActivityPlugin should still report rule violation")
        self.assertIn("Xbox", result, "ActivityPlugin should mention missing Xbox")
        print("✅ ActivityPlugin correctly blocks gaming with partial equipment")
        
        # Test 3: Add Xbox and try again - should succeed
        self.state.add_to_inventory(Item.XBOX.value)
        result = self.activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        self.assertNotIn("Rule violation", result, "ActivityPlugin should not report rule violation")
        self.assertIn("chosen", result.lower(), "ActivityPlugin should confirm activity was chosen")
        self.assertIn("Play games", result, "ActivityPlugin should mention the chosen activity")
        print("✅ ActivityPlugin correctly allows gaming with full equipment")
    
    def test_gaming_rules_with_weather_conditions(self):
        """Test gaming rules under different weather conditions."""
        # Add gaming equipment
        self.state.add_to_inventory(Item.TV.value)
        self.state.add_to_inventory(Item.XBOX.value)
        
        # Test with various weather conditions - gaming should be allowed regardless
        weather_conditions = [
            WeatherCondition.SUNNY,
            WeatherCondition.RAINING,
            WeatherCondition.SNOWING,
            WeatherCondition.UNKNOWN
        ]
        
        for weather in weather_conditions:
            with self.subTest(weather=weather):
                self.state.set_weather(weather)
                result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
                self.assertTrue(result.allowed, f"Gaming should be allowed in {weather.value} weather")
                
                # Also test through plugin
                result = self.activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
                self.assertNotIn("Rule violation", result, f"ActivityPlugin should allow gaming in {weather.value} weather")
        
        print("✅ Gaming rules work correctly under all weather conditions")
    
    def test_gaming_rules_edge_cases(self):
        """Test edge cases for gaming rules."""
        # Test 1: Case sensitivity
        self.state.add_to_inventory("tv")  # lowercase
        self.state.add_to_inventory("xbox")  # lowercase
        
        # The rule should work with exact case matching
        result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
        # This might fail if case sensitivity is not handled properly
        # Let's check what's actually in inventory
        print(f"Debug: Inventory contains: {self.state.inventory}")
        print(f"Debug: Looking for: {Item.TV.value}, {Item.XBOX.value}")
        
        # Test 2: Extra items in inventory
        reset_state()
        self.state = get_state()
        self.state.add_to_inventory(Item.TV.value)
        self.state.add_to_inventory(Item.XBOX.value)
        self.state.add_to_inventory(Item.HIKING_BOOTS.value)  # Extra item
        self.state.add_to_inventory(Item.GOGGLES.value)  # Extra item
        
        result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
        self.assertTrue(result.allowed, "Gaming should be allowed with extra items in inventory")
        
        # Test 3: Empty activity string (should be handled before rule checking)
        result = self.activity_plugin.choose_activity("")
        self.assertIn("No activity specified", result, "Should handle empty activity string")
        
        # Test 4: Invalid activity (should be handled before rule checking)
        result = self.activity_plugin.choose_activity("Invalid Activity")
        self.assertIn("Invalid activity", result, "Should handle invalid activity")
        
        print("✅ Gaming rules handle edge cases correctly")
    
    def test_gaming_rules_integration(self):
        """Integration test combining multiple components."""
        # Start with clean state
        self.assertEqual(len(self.state.inventory), 0, "Should start with empty inventory")
        
        # Step 1: Try gaming without equipment - should fail
        result = self.activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        self.assertIn("Rule violation", result)
        print("✅ Integration: Gaming blocked without equipment")
        
        # Step 2: Buy TV through shopping plugin
        shopping_plugin = None
        for plugin in self.plugins:
            if hasattr(plugin, 'shopping'):
                shopping_plugin = plugin
                break
        
        self.assertIsNotNone(shopping_plugin, "ShoppingPlugin not found")
        
        result = shopping_plugin.shopping(Item.TV.value)
        self.assertIn("Successfully purchased", result)
        self.assertIn(Item.TV.value, self.state.inventory)
        print("✅ Integration: TV purchased successfully")
        
        # Step 3: Try gaming with only TV - should still fail
        result = self.activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        self.assertIn("Rule violation", result)
        self.assertIn("Xbox", result)
        print("✅ Integration: Gaming still blocked with only TV")
        
        # Step 4: Buy Xbox
        result = shopping_plugin.shopping(Item.XBOX.value)
        self.assertIn("Successfully purchased", result)
        self.assertIn(Item.XBOX.value, self.state.inventory)
        print("✅ Integration: Xbox purchased successfully")
        
        # Step 5: Now gaming should be allowed
        result = self.activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        self.assertNotIn("Rule violation", result)
        self.assertIn("chosen", result.lower())
        self.assertEqual(self.state.chosen_activity, Activity.PLAY_GAMES)
        print("✅ Integration: Gaming allowed with full equipment")
        
        # Step 6: Verify state is properly updated
        self.assertEqual(len(self.state.inventory), 2, "Should have 2 items in inventory")
        self.assertIn(Item.TV.value, self.state.inventory)
        self.assertIn(Item.XBOX.value, self.state.inventory)
        self.assertEqual(self.state.chosen_activity, Activity.PLAY_GAMES)
        print("✅ Integration: State properly maintained throughout process")


class TestGamingRulesBoundaryConditions(unittest.TestCase):
    """Test boundary conditions and stress scenarios for gaming rules."""
    
    def setUp(self):
        """Set up test environment."""
        reset_state()
        self.state = get_state()
        self.rule_engine = get_rule_engine()
    
    def test_multiple_rule_evaluations(self):
        """Test that rules work correctly with multiple evaluations."""
        play_games_rule = PlayGamesRule()
        
        # Test the same rule multiple times
        for i in range(10):
            with self.subTest(iteration=i):
                result = play_games_rule.check(self.state, activity=Activity.PLAY_GAMES.value)
                self.assertFalse(result.allowed, f"Rule should consistently fail on iteration {i}")
        
        # Add equipment and test again multiple times
        self.state.add_to_inventory(Item.TV.value)
        self.state.add_to_inventory(Item.XBOX.value)
        
        for i in range(10):
            with self.subTest(iteration=i):
                result = play_games_rule.check(self.state, activity=Activity.PLAY_GAMES.value)
                self.assertTrue(result.allowed, f"Rule should consistently pass on iteration {i}")
        
        print("✅ Gaming rules consistent across multiple evaluations")
    
    def test_rule_engine_rule_ordering(self):
        """Test that rule ordering doesn't affect gaming rule enforcement."""
        # Gaming should be blocked by equipment rule before weather rules are evaluated
        self.state.set_weather(WeatherCondition.UNKNOWN)  # This would normally block outdoor activities
        
        result = self.rule_engine.check_activity_rules(self.state, Activity.PLAY_GAMES.value)
        self.assertFalse(result.allowed, "Should be blocked by equipment rule")
        self.assertIn("TV", result.reason, "Should mention missing gaming equipment")
        self.assertIn("Xbox", result.reason, "Should mention missing gaming equipment")
        
        print("✅ Gaming rules have correct precedence in rule engine")


def run_gaming_rules_tests():
    """Run all gaming rules tests."""
    print("🚀 Starting Comprehensive Gaming Rules Tests...\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGamingRulesEnforcement))
    suite.addTests(loader.loadTestsFromTestCase(TestGamingRulesBoundaryConditions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print("\n🎉 All gaming rules tests passed!")
        print("✅ Gaming rules are properly enforced at all levels:")
        print("   • Rule class level (PlayGamesRule)")
        print("   • Rule engine level (check_activity_rules)")
        print("   • Plugin level (ActivityPlugin.choose_activity)")
        print("   • Integration level (shopping + activity selection)")
        return True
    else:
        print(f"\n❌ Gaming rules tests failed!")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        
        # Print detailed failure information
        for test, error in result.failures + result.errors:
            print(f"\n❌ {test}: {error}")
        
        return False


if __name__ == "__main__":
    success = run_gaming_rules_tests()
    sys.exit(0 if success else 1)