"""
Semantic Kernel tools/functions for the policy enforcer agent.

This module provides Semantic Kernel functions with business rule enforcement,
maintaining the policy enforcement pattern.
"""

import random
from typing import Annotated, Optional

from semantic_kernel.functions import kernel_function

from .state import get_state, WeatherCondition, Activity
from .rules import get_rule_engine
from .items import Item, ItemRequirements


class PolicyEnforcedPlugin:
    """
    Base class for Semantic Kernel plugins with policy enforcement.
    
    This provides the policy enforcement pattern using
    Semantic Kernel's function decoration approach.
    """
    
    def check_tool_rules(self, tool_name: str, **kwargs) -> Optional[str]:
        """Check tool-specific business rules."""
        state = get_state()
        rule_engine = get_rule_engine()
        
        # Check general tool-specific rules
        result = rule_engine.check_tool_rules(state, tool_name=tool_name)
        if not result.allowed:
            return result.reason
        
        return None
    
    def check_activity_rules(self, activity: str) -> Optional[str]:
        """Check activity-specific rules."""
        state = get_state()
        rule_engine = get_rule_engine()
        
        result = rule_engine.check_activity_rules(state, activity)
        if not result.allowed:
            return result.reason
        
        return None


class WeatherPlugin(PolicyEnforcedPlugin):
    """Plugin for weather-related functions."""
    
    @kernel_function(
        description="Check the current weather condition. Returns a random weather condition.",
        name="check_weather"
    )
    def check_weather(self) -> Annotated[str, "Current weather condition with status"]:
        """Check the weather condition."""
        # Check rules first
        rule_violation = self.check_tool_rules("check_weather")
        if rule_violation:
            return f"❌ Rule violation: {rule_violation}"
        
        state = get_state()
        
        # Generate random weather
        weather_options = [WeatherCondition.SUNNY, WeatherCondition.RAINING, WeatherCondition.SNOWING]

        if state.weather_checked and state.weather != WeatherCondition.UNKNOWN:
            return (f"🌤️ Weather already checked! Current weather: {state.weather.value}\n"
                    f"📊 Weather status: Known and checked")
        
        new_weather = random.choice(weather_options)
        
        # Update state
        state.set_weather(new_weather)
        
        return (f"🌤️ Weather check complete! Current weather: {new_weather.value}\n"
                f"📊 Weather status: Known and checked")


class ShoppingPlugin(PolicyEnforcedPlugin):
    """Plugin for shopping-related functions."""
    
    @kernel_function(
        description="Purchase an item and add it to your inventory. Available items: TV, Xbox, Hiking Boots, Goggles, Sunscreen",
        name="shopping"
    )
    def shopping(
        self, 
        item: Annotated[str, "The item to purchase: TV, Xbox, Hiking Boots, Goggles, or Sunscreen"]
    ) -> Annotated[str, "Result of the shopping action with updated inventory"]:
        """Purchase an item."""
        if not item:
            return "❌ No item specified for purchase."
        
        # Check rules first
        rule_violation = self.check_tool_rules("shopping", item=item)
        if rule_violation:
            return f"❌ Rule violation: {rule_violation}"
        
        # Validate the item first
        if not ItemRequirements.is_valid_item(item):
            available_items = ", ".join(ItemRequirements.get_all_items())
            return f"❌ Invalid item '{item}'. Available items: {available_items}"
        
        state = get_state()
        
        # Add item to inventory
        state.add_to_inventory(item)
        
        # Enhanced output with state information
        return (f"🛒 Successfully purchased: {item}. Added to inventory!\n"
                f"📊 Current inventory: {', '.join(sorted(state.inventory)) if state.inventory else 'Empty'}")


class ActivityPlugin(PolicyEnforcedPlugin):
    """Plugin for activity-related functions."""
    
    @kernel_function(
        description="Choose an activity from: 'Play games', 'Go Camping', or 'Swimming'. The choice will be validated against business rules.",
        name="choose_activity"
    )
    def choose_activity(
        self, 
        activity: Annotated[str, "The activity to choose: 'Play games', 'Go Camping', or 'Swimming'"]
    ) -> Annotated[str, "Result of choosing the activity with current state"]:
        """Choose an activity."""
        if not activity:
            return "❌ No activity specified."
        
        # Validate activity format FIRST, before rule checking
        valid_activities = [a.value for a in Activity]
        if activity not in valid_activities:
            return f"❌ Invalid activity. Choose from: {', '.join(valid_activities)}"
        
        # Check activity-specific rules
        rule_violation = self.check_activity_rules(activity)
        if rule_violation:
            return f"❌ Rule violation: {rule_violation}"
        
        # Check general tool rules
        tool_rule_violation = self.check_tool_rules("choose_activity", activity=activity)
        if tool_rule_violation:
            return f"❌ Rule violation: {tool_rule_violation}"
        
        state = get_state()
        
        # Set the chosen activity (validation already done)
        activity_enum = Activity(activity)
        state.set_activity(activity_enum)
        
        return (f"🎯 Activity chosen: {activity}! Have fun!\n"
                f"📊 Current activity: {activity}\n"
                f"📊 Current inventory: {', '.join(sorted(state.inventory)) if state.inventory else 'Empty'}")


class StatePlugin(PolicyEnforcedPlugin):
    """Plugin for state management functions."""
    
    @kernel_function(
        description="Check the current state including inventory, weather, and chosen activity.",
        name="check_state"
    )
    def check_state(self) -> Annotated[str, "Current agent state information"]:
        """Check the current agent state."""
        # No rule checking needed for state inspection
        state = get_state()
        
        return (f"📊 **Current Agent State:**\n"
                f"🎒 Inventory: {', '.join(sorted(state.inventory)) if state.inventory else 'Empty'}\n"
                f"🌤️ Weather: {state.weather.value} ({'Known' if state.weather_checked else 'Unknown'})\n"
                f"🎯 Current Activity: {state.chosen_activity.value if state.chosen_activity else 'None chosen'}")


def get_plugins() -> list:
    """Get all plugins for the policy enforcer."""
    return [
        WeatherPlugin(),
        ShoppingPlugin(), 
        ActivityPlugin(),
        StatePlugin()
    ]