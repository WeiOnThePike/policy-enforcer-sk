#!/usr/bin/env python3
"""
Comprehensive end-to-end test for all gaming rule scenarios.
This test demonstrates that gaming rules are properly enforced
in all possible combinations and edge cases.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from policy_enforcer.state import get_state, reset_state, WeatherCondition, Activity
from policy_enforcer.rules import get_rule_engine
from policy_enforcer.tools import get_plugins
from policy_enforcer.items import Item


def test_all_gaming_scenarios():
    """Test all possible gaming scenarios comprehensively."""
    print("🎮 COMPREHENSIVE GAMING RULES TEST")
    print("=" * 50)
    
    plugins = get_plugins()
    rule_engine = get_rule_engine()
    
    # Get plugins
    shopping_plugin = None
    activity_plugin = None
    for plugin in plugins:
        if hasattr(plugin, 'shopping'):
            shopping_plugin = plugin
        if hasattr(plugin, 'choose_activity'):
            activity_plugin = plugin
    
    scenarios = [
        {
            "name": "Empty Inventory",
            "setup": lambda: None,
            "expected": False,
            "reason_contains": ["TV", "Xbox"]
        },
        {
            "name": "Only TV (correct case)",
            "setup": lambda: shopping_plugin.shopping("TV"),
            "expected": False,
            "reason_contains": ["Xbox"]
        },
        {
            "name": "Only TV (lowercase)",
            "setup": lambda: shopping_plugin.shopping("tv"),
            "expected": False,
            "reason_contains": ["Xbox"]
        },
        {
            "name": "Only Xbox (correct case)",
            "setup": lambda: shopping_plugin.shopping("Xbox"),
            "expected": False,
            "reason_contains": ["TV"],
            "reset_first": True
        },
        {
            "name": "Only Xbox (lowercase)",
            "setup": lambda: shopping_plugin.shopping("xbox"),
            "expected": False,
            "reason_contains": ["TV"],
            "reset_first": True
        },
        {
            "name": "Both TV and Xbox (correct case)",
            "setup": lambda: [shopping_plugin.shopping("TV"), shopping_plugin.shopping("Xbox")],
            "expected": True,
            "reason_contains": [],
            "reset_first": True
        },
        {
            "name": "Both TV and Xbox (mixed case)",
            "setup": lambda: [shopping_plugin.shopping("tv"), shopping_plugin.shopping("XBOX")],
            "expected": True,
            "reason_contains": [],
            "reset_first": True
        },
        {
            "name": "All gaming items + extras",
            "setup": lambda: [
                shopping_plugin.shopping("TV"),
                shopping_plugin.shopping("Xbox"),
                shopping_plugin.shopping("Hiking Boots"),
                shopping_plugin.shopping("Goggles")
            ],
            "expected": True,
            "reason_contains": [],
            "reset_first": True
        },
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print("-" * 30)
        
        # Reset state for each scenario
        reset_state()
        state = get_state()
        
        # Setup scenario
        if scenario['setup']:
            setup_result = scenario['setup']()
            # Handle list of operations
            if isinstance(setup_result, list):
                pass  # Just execute the list
            # Single operation already executed
        
        print(f"   Inventory: {list(state.inventory) if state.inventory else 'Empty'}")
        
        # Test through rule engine
        rule_result = rule_engine.check_activity_rules(state, Activity.PLAY_GAMES.value)
        print(f"   Rule Engine: {'✅ Allowed' if rule_result.allowed else '❌ Blocked'}")
        if not rule_result.allowed:
            print(f"   Rule Reason: {rule_result.reason}")
        
        # Test through activity plugin
        plugin_result = activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        plugin_allowed = "Rule violation" not in plugin_result
        print(f"   Activity Plugin: {'✅ Allowed' if plugin_allowed else '❌ Blocked'}")
        if not plugin_allowed:
            print(f"   Plugin Response: {plugin_result}")
        
        # Verify expectations
        rule_match = rule_result.allowed == scenario['expected']
        plugin_match = plugin_allowed == scenario['expected']
        
        if scenario['expected'] and scenario['reason_contains']:
            reason_match = True  # No reason expected for allowed scenarios
        elif not scenario['expected'] and scenario['reason_contains']:
            reason_match = all(item in rule_result.reason for item in scenario['reason_contains'])
        else:
            reason_match = True
        
        scenario_passed = rule_match and plugin_match and reason_match
        
        if scenario_passed:
            print(f"   Result: ✅ PASSED")
        else:
            print(f"   Result: ❌ FAILED")
            print(f"      Expected: {'Allowed' if scenario['expected'] else 'Blocked'}")
            print(f"      Rule Engine: {'Allowed' if rule_result.allowed else 'Blocked'}")
            print(f"      Activity Plugin: {'Allowed' if plugin_allowed else 'Blocked'}")
            if scenario['reason_contains'] and not reason_match:
                print(f"      Expected reason to contain: {scenario['reason_contains']}")
                print(f"      Actual reason: {rule_result.reason}")
            all_passed = False
    
    # Test weather independence for gaming
    print(f"\n{len(scenarios) + 1}. Testing: Gaming with Different Weather Conditions")
    print("-" * 50)
    
    weather_conditions = [
        WeatherCondition.SUNNY,
        WeatherCondition.RAINING,
        WeatherCondition.SNOWING,
        WeatherCondition.UNKNOWN
    ]
    
    reset_state()
    state = get_state()
    shopping_plugin.shopping("TV")
    shopping_plugin.shopping("Xbox")
    
    for weather in weather_conditions:
        state.set_weather(weather)
        result = rule_engine.check_activity_rules(state, Activity.PLAY_GAMES.value)
        weather_passed = result.allowed
        
        print(f"   Weather {weather.value}: {'✅ Allowed' if weather_passed else '❌ Blocked'}")
        if not weather_passed:
            print(f"   Reason: {result.reason}")
            all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL GAMING SCENARIOS PASSED!")
        print("\n✅ Gaming rules are properly enforced:")
        print("   • Requires both TV and Xbox")
        print("   • Works with any case (tv, TV, xbox, Xbox, etc.)")
        print("   • Blocks partial equipment")
        print("   • Allows extra items in inventory")
        print("   • Works independently of weather conditions")
        print("   • Consistent between rule engine and activity plugin")
        print("   • Provides clear error messages")
    else:
        print("❌ SOME GAMING SCENARIOS FAILED!")
        print("Gaming rules need further investigation.")
    
    return all_passed


if __name__ == "__main__":
    success = test_all_gaming_scenarios()
    sys.exit(0 if success else 1)