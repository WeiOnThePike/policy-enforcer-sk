"""Unit tests for state management module."""

import pytest
from policy_enforcer.state import (
    get_state, reset_state, AgentState, WeatherCondition, Activity
)
from policy_enforcer.items import Item


class TestAgentState:
    """Test AgentState class."""
    
    def test_initial_state(self):
        """Test initial state is correct."""
        state = AgentState()
        assert state.inventory == set()
        assert state.weather == WeatherCondition.UNKNOWN
        assert state.weather_checked is False
        assert state.chosen_activity is None
    
    def test_add_to_inventory(self):
        """Test adding items to inventory."""
        state = AgentState()
        
        # Add valid item
        state.add_to_inventory("TV")
        assert "TV" in state.inventory
        
        # Add another item
        state.add_to_inventory("Xbox")
        assert "Xbox" in state.inventory
        assert len(state.inventory) == 2
    
    def test_add_to_inventory_case_insensitive(self):
        """Test adding items is case insensitive."""
        state = AgentState()
        
        state.add_to_inventory("tv")
        assert "TV" in state.inventory
        
        state.add_to_inventory("XBOX")
        assert "Xbox" in state.inventory
    
    def test_add_invalid_item_to_inventory(self):
        """Test adding invalid item doesn't validate (handled by plugins)."""
        state = AgentState()
        
        # Invalid items are added but not validated at state level
        state.add_to_inventory("InvalidItem")
        assert "InvalidItem" in state.inventory
    
    def test_has_item(self):
        """Test checking if state has item."""
        state = AgentState()
        
        assert not state.has_item("TV")
        
        state.add_to_inventory("TV")
        assert state.has_item("TV")
        # has_item is case sensitive - normalization happens in add_to_inventory
        assert not state.has_item("tv")
    
    def test_has_items(self):
        """Test checking if state has multiple items."""
        state = AgentState()
        
        assert not state.has_items(["TV", "Xbox"])
        
        state.add_to_inventory("TV")
        assert not state.has_items(["TV", "Xbox"])
        
        state.add_to_inventory("Xbox")
        assert state.has_items(["TV", "Xbox"])
    
    def test_set_weather(self):
        """Test setting weather."""
        state = AgentState()
        
        state.set_weather(WeatherCondition.SUNNY)
        assert state.weather == WeatherCondition.SUNNY
        assert state.weather_checked is True
    
    def test_set_activity(self):
        """Test setting activity."""
        state = AgentState()
        
        state.set_activity(Activity.PLAY_GAMES)
        assert state.chosen_activity == Activity.PLAY_GAMES
    
    def test_get_summary(self):
        """Test get_summary method."""
        state = AgentState()
        summary = state.get_summary()
        
        assert "Inventory: Empty" in summary
        assert "Weather: unknown" in summary
        assert "Weather checked: False" in summary
        
        # Add items and change state
        state.add_to_inventory("TV")
        state.set_weather(WeatherCondition.SUNNY)
        state.set_activity(Activity.PLAY_GAMES)
        
        summary = state.get_summary()
        assert "TV" in summary
        assert "sunny" in summary
        assert "Play games" in summary


class TestStateManagement:
    """Test state management functions."""
    
    def test_get_state_singleton(self):
        """Test get_state returns same instance."""
        state1 = get_state()
        state2 = get_state()
        assert state1 is state2
    
    def test_reset_state(self):
        """Test reset_state clears everything."""
        state = get_state()
        
        # Modify state
        state.add_to_inventory("TV")
        state.set_weather(WeatherCondition.SUNNY)
        state.set_activity(Activity.PLAY_GAMES)
        
        # Reset and verify
        reset_state()
        state = get_state()
        
        assert state.inventory == set()
        assert state.weather == WeatherCondition.UNKNOWN
        assert state.weather_checked is False
        assert state.chosen_activity is None


class TestEnums:
    """Test enum classes."""
    
    def test_weather_condition_values(self):
        """Test WeatherCondition enum values."""
        assert WeatherCondition.UNKNOWN.value == "unknown"
        assert WeatherCondition.SUNNY.value == "sunny"
        assert WeatherCondition.RAINING.value == "raining"
        assert WeatherCondition.SNOWING.value == "snowing"
    
    def test_activity_values(self):
        """Test Activity enum values."""
        assert Activity.PLAY_GAMES.value == "Play games"
        assert Activity.GO_CAMPING.value == "Go Camping"
        assert Activity.SWIMMING.value == "Swimming"