"""
State management for the policy enforcer agent.
"""

from typing import Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum


class WeatherCondition(str, Enum):
    """Weather conditions."""
    SUNNY = "sunny"
    RAINING = "raining"
    SNOWING = "snowing"
    UNKNOWN = "unknown"


class Activity(str, Enum):
    """Available activities."""
    PLAY_GAMES = "Play games"
    GO_CAMPING = "Go Camping"
    SWIMMING = "Swimming"


class AgentState(BaseModel):
    """
    Tracks the current state of the agent including user inventory,
    weather conditions, and activity choices.
    """
    
    # User inventory
    inventory: Set[str] = Field(default_factory=set, description="Items the user owns")
    
    # Weather state
    weather: WeatherCondition = Field(default=WeatherCondition.UNKNOWN, description="Current weather condition")
    weather_checked: bool = Field(default=False, description="Whether weather has been checked")
    
    # Activity state
    chosen_activity: Optional[Activity] = Field(default=None, description="User's chosen activity")
    
    # Shopping history
    shopping_history: list[str] = Field(default_factory=list, description="Items purchased")
    
    def add_to_inventory(self, item: str) -> None:
        """Add an item to the user's inventory with normalized case."""
        from ..items import ItemRequirements
        # Normalize the item name to correct case
        normalized_item = ItemRequirements.normalize_item_name(item)
        self.inventory.add(normalized_item)
        self.shopping_history.append(normalized_item)
    
    def has_item(self, item: str) -> bool:
        """Check if user has a specific item."""
        return item in self.inventory
    
    def has_items(self, items: list[str]) -> bool:
        """Check if user has all required items."""
        return all(self.has_item(item) for item in items)
    
    def set_weather(self, weather: WeatherCondition) -> None:
        """Set the weather condition."""
        self.weather = weather
        self.weather_checked = True
    
    def set_activity(self, activity: Activity) -> None:
        """Set the chosen activity."""
        self.chosen_activity = activity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for easy inspection."""
        return {
            "inventory": list(self.inventory),
            "weather": self.weather.value,
            "weather_checked": self.weather_checked,
            "chosen_activity": self.chosen_activity.value if self.chosen_activity else None,
            "shopping_history": self.shopping_history
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the current state."""
        summary = []
        summary.append(f"Inventory: {', '.join(self.inventory) if self.inventory else 'Empty'}")
        summary.append(f"Weather: {self.weather.value}")
        summary.append(f"Weather checked: {self.weather_checked}")
        if self.chosen_activity:
            summary.append(f"Chosen activity: {self.chosen_activity.value}")
        return "\n".join(summary)


# Global state instance
agent_state = AgentState()


def get_state() -> AgentState:
    """Get the current agent state."""
    return agent_state


def reset_state() -> None:
    """Reset the agent state to initial values."""
    global agent_state
    agent_state = AgentState()
