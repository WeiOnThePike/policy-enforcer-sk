"""Unit tests for tools/plugins module."""

import pytest
from unittest.mock import patch, MagicMock
from policy_enforcer.tools import (
    get_plugins, ShoppingPlugin, ActivityPlugin, WeatherPlugin, StatePlugin
)
from policy_enforcer.state import get_state, reset_state, WeatherCondition, Activity
from policy_enforcer.items import Item


class TestShoppingPlugin:
    """Test ShoppingPlugin class."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_shopping_valid_item(self):
        """Test shopping for valid item."""
        plugin = ShoppingPlugin()
        result = plugin.shopping("TV")
        
        state = get_state()
        assert "TV" in state.inventory
        assert "Successfully purchased: TV" in result
    
    def test_shopping_invalid_item(self):
        """Test shopping for invalid item."""
        plugin = ShoppingPlugin()
        result = plugin.shopping("InvalidItem")
        
        state = get_state()
        assert "InvalidItem" not in state.inventory
        assert "Invalid item 'InvalidItem'" in result
        assert "Available items:" in result
    
    def test_shopping_case_insensitive(self):
        """Test shopping is case insensitive."""
        plugin = ShoppingPlugin()
        result = plugin.shopping("tv")
        
        state = get_state()
        assert "TV" in state.inventory  # Inventory stores normalized name
        assert "Successfully purchased: tv" in result  # Result shows original input


class TestActivityPlugin:
    """Test ActivityPlugin class."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_choose_activity_gaming_success(self):
        """Test choosing gaming activity successfully."""
        state = get_state()
        state.add_to_inventory("TV")
        state.add_to_inventory("Xbox")
        
        plugin = ActivityPlugin()
        result = plugin.choose_activity("Play games")
        
        assert state.chosen_activity == Activity.PLAY_GAMES
        assert "Activity chosen: Play games" in result
    
    def test_choose_activity_gaming_failure(self):
        """Test choosing gaming activity with missing items."""
        plugin = ActivityPlugin()
        result = plugin.choose_activity("Play games")
        
        state = get_state()
        assert state.chosen_activity is None
        assert "Rule violation" in result
        assert "TV" in result or "Xbox" in result
    
    def test_choose_activity_camping_success(self):
        """Test choosing camping activity successfully."""
        state = get_state()
        state.add_to_inventory("Hiking Boots")
        state.set_weather(WeatherCondition.SUNNY)
        
        plugin = ActivityPlugin()
        result = plugin.choose_activity("Go Camping")
        
        assert state.chosen_activity == Activity.GO_CAMPING
        assert "Activity chosen: Go Camping" in result
    
    def test_choose_activity_invalid(self):
        """Test choosing invalid activity."""
        plugin = ActivityPlugin()
        result = plugin.choose_activity("Invalid Activity")
        
        assert "Invalid activity" in result
        assert "Choose from:" in result


class TestWeatherPlugin:
    """Test WeatherPlugin class."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    @patch('random.choice')
    def test_check_weather_success(self, mock_choice):
        """Test checking weather successfully."""
        mock_choice.return_value = WeatherCondition.SUNNY
        
        plugin = WeatherPlugin()
        result = plugin.check_weather()
        
        state = get_state()
        assert state.weather == WeatherCondition.SUNNY
        assert state.weather_checked is True
        assert "Weather check complete" in result
        assert "sunny" in result
    
    def test_check_weather_already_checked(self):
        """Test checking weather when already checked."""
        state = get_state()
        state.set_weather(WeatherCondition.SUNNY)  # This sets weather_checked = True
        
        plugin = WeatherPlugin()
        result = plugin.check_weather()
        
        assert "Rule violation" in result
        assert "already been checked" in result


class TestStatePlugin:
    """Test StatePlugin class."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_check_state_empty(self):
        """Test checking state when empty."""
        plugin = StatePlugin()
        result = plugin.check_state()
        
        assert "Current Agent State:" in result
        assert "Inventory: Empty" in result
        assert "Weather: unknown" in result
        assert "Current Activity: None chosen" in result
    
    def test_check_state_with_data(self):
        """Test checking state with data."""
        state = get_state()
        state.add_to_inventory("TV")
        state.add_to_inventory("Xbox")
        state.set_weather(WeatherCondition.SUNNY)
        state.set_activity(Activity.PLAY_GAMES)
        
        plugin = StatePlugin()
        result = plugin.check_state()
        
        assert "TV" in result
        assert "Xbox" in result
        assert "sunny" in result
        assert "Play games" in result


class TestPluginManagement:
    """Test plugin management functions."""
    
    def test_get_plugins(self):
        """Test getting all plugins."""
        plugins = get_plugins()
        
        assert len(plugins) == 4
        
        plugin_types = [type(plugin).__name__ for plugin in plugins]
        assert "ShoppingPlugin" in plugin_types
        assert "ActivityPlugin" in plugin_types
        assert "WeatherPlugin" in plugin_types
        assert "StatePlugin" in plugin_types
    
    def test_plugins_have_rule_checks(self):
        """Test that all plugins have rule checking methods."""
        plugins = get_plugins()
        
        for plugin in plugins:
            assert hasattr(plugin, 'check_activity_rules')
            assert hasattr(plugin, 'check_tool_rules')
            assert callable(getattr(plugin, 'check_activity_rules'))
            assert callable(getattr(plugin, 'check_tool_rules'))


class TestPluginRuleIntegration:
    """Test plugin integration with rule engine."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_activity_plugin_rule_integration(self):
        """Test activity plugin integrates with rule engine."""
        plugin = ActivityPlugin()
        state = get_state()
        
        # Test rule checking - check_activity_rules returns violation string or None
        rule_violation = plugin.check_activity_rules(Activity.PLAY_GAMES.value)
        assert rule_violation is not None  # Should have violation for missing items
        assert "TV" in rule_violation or "Xbox" in rule_violation
        
        # Add required items
        state.add_to_inventory("TV")
        state.add_to_inventory("Xbox")
        
        rule_violation = plugin.check_activity_rules(Activity.PLAY_GAMES.value)
        assert rule_violation is None  # No violation when items are present
    
    def test_weather_plugin_rule_integration(self):
        """Test weather plugin integrates with rule engine."""
        plugin = WeatherPlugin()
        state = get_state()
        
        # Test rule checking - check_tool_rules returns violation string or None
        rule_violation = plugin.check_tool_rules("check_weather")
        assert rule_violation is None  # Should be allowed initially
        
        # Check weather
        plugin.check_weather()
        
        # Test rule checking - should be blocked now
        rule_violation = plugin.check_tool_rules("check_weather")
        assert rule_violation is not None  # Should have violation
        assert "already been checked" in rule_violation