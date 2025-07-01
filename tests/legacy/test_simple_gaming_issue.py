#!/usr/bin/env python3
"""
Simple test to demonstrate the gaming rules issue.
This test will show the bug where gaming is allowed with only Xbox.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gaming_with_xbox_only():
    """Test that should demonstrate the bug."""
    try:
        from policy_enforcer.state import get_state, reset_state, Activity
        from policy_enforcer.rules import get_rule_engine, PlayGamesRule
        from policy_enforcer.tools import ActivityPlugin
        from policy_enforcer.items import Item, ItemRequirements
        
        print("🔍 Testing gaming rules with Xbox only...")
        
        # Reset state and get components
        reset_state()
        state = get_state()
        rule_engine = get_rule_engine()
        activity_plugin = ActivityPlugin()
        
        # Add only Xbox to inventory
        state.add_to_inventory(Item.XBOX.value)
        print(f"📦 Inventory: {list(state.inventory)}")
        
        # Test 1: Check missing items directly
        missing_items = ItemRequirements.get_missing_items(Activity.PLAY_GAMES.value, state.inventory)
        print(f"❓ Missing items for gaming: {[item.value for item in missing_items]}")
        
        # Test 2: Check PlayGamesRule directly
        play_games_rule = PlayGamesRule()
        rule_result = play_games_rule.check(state, activity=Activity.PLAY_GAMES.value)
        print(f"🔧 PlayGamesRule result: allowed={rule_result.allowed}, reason={rule_result.reason}")
        
        # Test 3: Check rule engine
        engine_result = rule_engine.check_activity_rules(state, Activity.PLAY_GAMES.value)
        print(f"⚙️ RuleEngine result: allowed={engine_result.allowed}, reason={engine_result.reason}")
        
        # Test 4: Check activity plugin
        plugin_result = activity_plugin.choose_activity(Activity.PLAY_GAMES.value)
        print(f"🎮 ActivityPlugin result: {plugin_result}")
        
        # Analysis
        print("\n📊 Analysis:")
        print(f"- Xbox in inventory: {'Xbox' in state.inventory}")
        print(f"- TV in inventory: {'TV' in state.inventory}")
        print(f"- Required items: {[item.value for item in ItemRequirements.PLAY_GAMES]}")
        
        # The bug is if plugin allows gaming when it should be blocked
        if "Rule violation" not in plugin_result:
            print("🚨 BUG FOUND: ActivityPlugin allowed gaming with only Xbox!")
            return False
        else:
            print("✅ ActivityPlugin correctly blocked gaming with only Xbox")
            return True
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("This might be due to missing dependencies like pydantic")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gaming_with_xbox_only()
    if not success:
        print("\n🔍 The issue appears to be in the rule checking logic.")
        print("Check the ItemRequirements.get_missing_items method and case sensitivity.")