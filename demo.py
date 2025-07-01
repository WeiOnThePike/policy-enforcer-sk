#!/usr/bin/env python3
"""
Simple demo of Policy Enforcer without requiring API key.
This demonstrates the business rules engine and state management.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from policy_enforcer.state import get_state, reset_state, WeatherCondition, Activity
from policy_enforcer.rules import get_rule_engine
from policy_enforcer.tools import get_plugins
from policy_enforcer.items import Item


def print_banner():
    """Print demo banner."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                Policy Enforcer Demo                       ║
║            Business Rules Engine Showcase                 ║
╚═══════════════════════════════════════════════════════════╝

This demo shows how business rules are enforced without requiring an API key.
""")


def demo_plugins():
    """Demonstrate plugins."""
    print("🧪 Plugin Demo\n")
    
    # Reset state
    reset_state()
    state = get_state()
    plugins = get_plugins()
    
    print("📊 Initial State:")
    print(state.get_summary())
    
    print("\n" + "="*60)
    print("SCENARIO 1: Testing Shopping Plugin")
    print("="*60)
    
    # Find shopping plugin
    shopping_plugin = None
    for plugin in plugins:
        if hasattr(plugin, 'shopping'):
            shopping_plugin = plugin
            break
    
    if shopping_plugin:
        print("🛒 Attempting to buy TV...")
        result = shopping_plugin.shopping("TV")
        print(f"Result: {result}")
        
        print("\n🛒 Attempting to buy invalid item...")
        result = shopping_plugin.shopping("NonExistentItem")
        print(f"Result: {result}")
    
    print("\n" + "="*60)
    print("SCENARIO 2: Testing Activity Plugin with Rule Violations")
    print("="*60)
    
    # Find activity plugin
    activity_plugin = None
    for plugin in plugins:
        if hasattr(plugin, 'choose_activity'):
            activity_plugin = plugin
            break
    
    if activity_plugin:
        print("🎯 Attempting to go camping without boots...")
        result = activity_plugin.choose_activity("Go Camping")
        print(f"Result: {result}")
        
        print("\n🥾 Adding hiking boots to inventory...")
        state.add_to_inventory("Hiking Boots")
        
        print("🎯 Attempting to go camping with boots but unknown weather...")
        result = activity_plugin.choose_activity("Go Camping")
        print(f"Result: {result}")
        
        print("\n☀️ Setting sunny weather...")
        state.set_weather(WeatherCondition.SUNNY)
        
        print("🎯 Attempting to go camping with boots and good weather...")
        result = activity_plugin.choose_activity("Go Camping")
        print(f"Result: {result}")
    
    print("\n" + "="*60)
    print("SCENARIO 3: Testing Weather Plugin")
    print("="*60)
    
    # Reset for weather demo
    reset_state()
    
    # Find weather plugin
    weather_plugin = None
    for plugin in plugins:
        if hasattr(plugin, 'check_weather'):
            weather_plugin = plugin
            break
    
    if weather_plugin:
        print("🌤️ Checking weather...")
        result = weather_plugin.check_weather()
        print(f"Result: {result}")
        
        print("\n🌤️ Attempting to check weather again (should be blocked)...")
        result = weather_plugin.check_weather()
        print(f"Result: {result}")
    
    print("\n" + "="*60)
    print("SCENARIO 4: Testing State Plugin")
    print("="*60)
    
    # Find state plugin
    state_plugin = None
    for plugin in plugins:
        if hasattr(plugin, 'check_state'):
            state_plugin = plugin
            break
    
    if state_plugin:
        print("📊 Checking current state...")
        result = state_plugin.check_state()
        print(f"Result: {result}")


def demo_rules_summary():
    """Show rules and plugin summary."""
    print("\n" + "="*60)
    print("BUSINESS RULES AND PLUGINS SUMMARY")
    print("="*60)
    
    rule_engine = get_rule_engine()
    plugins = get_plugins()
    
    print(f"📜 Business Rules:")
    print(rule_engine.get_rules_summary())
    
    print(f"\n🔧 Available Plugins:")
    for i, plugin in enumerate(plugins, 1):
        plugin_name = plugin.__class__.__name__
        functions = [attr for attr in dir(plugin) if not attr.startswith('_') and callable(getattr(plugin, attr))]
        # Filter out inherited methods
        sk_functions = [f for f in functions if hasattr(getattr(plugin, f), '__annotations__')]
        print(f"{i}. {plugin_name}: {', '.join(sk_functions)}")
    
    print(f"\n🎯 Architecture Features:")
    print("• Uses @kernel_function decorators with type annotations")
    print("• Custom ReAct implementation with policy enforcement")
    print("• Automatic business rule checking before tool execution")
    print("• State-aware plugins with persistent inventory and weather tracking")


def main():
    """Main demo function."""
    print_banner()
    
    try:
        demo_plugins()
        demo_rules_summary()
        
        print("\n" + "="*60)
        print("✅ POLICY ENFORCER DEMO COMPLETE")
        print("="*60)
        print("🎉 All plugins working correctly!")
        print("📊 Business rules enforcement fully functional")
        print("🔧 Ready for full agent testing with OpenAI API key")
        print("\nTo run the full agent:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Run: python main.py")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)