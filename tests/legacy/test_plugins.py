#!/usr/bin/env python3
"""
Test script for Policy Enforcer plugins.

This script tests the basic functionality of the plugins and business rules
without requiring a Google API key.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from policy_enforcer.state import get_state, reset_state, WeatherCondition, Activity
from policy_enforcer.rules import get_rule_engine
from policy_enforcer.tools import get_plugins
from policy_enforcer.items import Item
from policy_enforcer.prompt_utils import generate_prompt_instructions


def test_state_management():
    """Test state management functionality."""
    print("🧪 Testing State Management...")
    
    # Reset state
    reset_state()
    state = get_state()
    
    # Test initial state
    assert state.weather == WeatherCondition.UNKNOWN
    assert len(state.inventory) == 0
    assert state.chosen_activity is None
    
    # Test state updates
    state.add_to_inventory("TV")
    state.add_to_inventory("Xbox")
    state.set_weather(WeatherCondition.SUNNY)
    state.set_activity(Activity.PLAY_GAMES)
    
    assert "TV" in state.inventory
    assert "Xbox" in state.inventory
    assert state.weather == WeatherCondition.SUNNY
    assert state.chosen_activity == Activity.PLAY_GAMES
    
    print("✅ State management tests passed!")


def test_rules_engine():
    """Test business rules engine."""
    print("🧪 Testing Rules Engine...")
    
    reset_state()
    state = get_state()
    rule_engine = get_rule_engine()
    
    # Test play games rule - should fail without equipment
    result = rule_engine.check_activity_rules(state, Activity.PLAY_GAMES.value)
    assert not result.allowed
    assert "TV" in result.reason and "Xbox" in result.reason
    
    # Add equipment and test again
    state.add_to_inventory("TV")
    state.add_to_inventory("Xbox")
    result = rule_engine.check_activity_rules(state, Activity.PLAY_GAMES.value)
    assert result.allowed
    
    # Test camping weather rule - first add required equipment
    state.add_to_inventory("Hiking Boots")
    state.set_weather(WeatherCondition.RAINING)
    result = rule_engine.check_activity_rules(state, Activity.GO_CAMPING.value)
    assert not result.allowed
    assert "rain" in result.reason.lower()
    
    print("✅ Rules engine tests passed!")


def test_plugins():
    """Test plugins."""
    print("🧪 Testing Plugins...")
    
    reset_state()
    plugins = get_plugins()
    
    # Check that we have all expected plugins
    plugin_names = [plugin.__class__.__name__ for plugin in plugins]
    expected_plugins = ["WeatherPlugin", "ShoppingPlugin", "ActivityPlugin", "StatePlugin"]
    
    for expected in expected_plugins:
        assert expected in plugin_names, f"Missing plugin: {expected}"
    
    # Test shopping plugin
    shopping_plugin = next(p for p in plugins if isinstance(p, type(plugins[1])))
    
    # Test valid item purchase
    result = shopping_plugin.shopping("TV")
    assert "Successfully purchased" in result
    assert "TV" in result
    
    # Test invalid item purchase
    result = shopping_plugin.shopping("InvalidItem")
    assert "Invalid item" in result
    
    print("✅ Plugin tests passed!")


def test_prompt_generation():
    """Test prompt generation for both modes."""
    print("🧪 Testing Prompt Generation...")
    
    # Test with rules
    prompt_with_rules = generate_prompt_instructions(True)
    assert "business rules" in prompt_with_rules.lower()
    assert "rule" in prompt_with_rules.lower()
    
    # Test without rules
    prompt_without_rules = generate_prompt_instructions(False)
    assert "learn from these failures" in prompt_without_rules.lower()
    assert "infer the underlying business constraints" in prompt_without_rules.lower()
    
    # Both should have state awareness instructions
    assert "STATE AWARENESS" in prompt_with_rules
    assert "STATE AWARENESS" in prompt_without_rules
    
    print("✅ Prompt generation tests passed!")


def test_rule_enforcement_in_plugins():
    """Test that plugins properly enforce rules."""
    print("🧪 Testing Rule Enforcement in Plugins...")
    
    reset_state()
    state = get_state()
    plugins = get_plugins()
    
    # Find the activity plugin
    activity_plugin = None
    for plugin in plugins:
        if hasattr(plugin, 'choose_activity'):
            activity_plugin = plugin
            break
    
    assert activity_plugin is not None, "ActivityPlugin not found"
    
    # Test camping without boots - should fail
    result = activity_plugin.choose_activity("Go Camping")
    assert "Rule violation" in result
    assert "Hiking Boots" in result
    
    # Add boots and set good weather, then test again - should succeed
    state.add_to_inventory("Hiking Boots")
    state.set_weather(WeatherCondition.SUNNY)
    result = activity_plugin.choose_activity("Go Camping")
    assert "chosen" in result.lower()
    assert "Go Camping" in result
    
    print("✅ Rule enforcement tests passed!")


def run_all_tests():
    """Run all plugin tests."""
    print("🚀 Starting Policy Enforcer Plugin Tests...\n")
    
    try:
        test_state_management()
        test_rules_engine()
        test_plugins()
        test_prompt_generation()
        test_rule_enforcement_in_plugins()
        
        print("\n🎉 All tests passed! Policy Enforcer plugins working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)