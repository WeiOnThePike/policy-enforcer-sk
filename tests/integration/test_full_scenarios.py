"""Full end-to-end scenario tests."""

import pytest
from policy_enforcer.state import get_state, reset_state, WeatherCondition, Activity
from policy_enforcer.tools import get_plugins


class TestCompleteScenarios:
    """Test complete user scenarios end-to-end."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_gaming_happy_path(self):
        """Test complete gaming scenario - happy path."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        
        # Step 1: Buy TV
        result = shopping_plugin.shopping("TV")
        assert "Successfully purchased: TV" in result
        
        # Step 2: Buy Xbox  
        result = shopping_plugin.shopping("Xbox")
        assert "Successfully purchased: Xbox" in result
        
        # Step 3: Play games
        result = activity_plugin.choose_activity("Play games")
        assert "Activity chosen: Play games" in result
        
        # Verify final state
        state = get_state()
        assert "TV" in state.inventory
        assert "Xbox" in state.inventory
        assert state.chosen_activity == Activity.PLAY_GAMES
    
    def test_camping_happy_path(self):
        """Test complete camping scenario - happy path."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        weather_plugin = next(p for p in plugins if hasattr(p, 'check_weather'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        
        # Step 1: Buy hiking boots
        result = shopping_plugin.shopping("Hiking Boots")
        assert "Successfully purchased: Hiking Boots" in result
        
        # Step 2: Check weather
        result = weather_plugin.check_weather()
        assert "Weather check complete" in result
        
        # Step 3: Go camping (weather permitting)
        state = get_state()
        if state.weather != WeatherCondition.RAINING:
            result = activity_plugin.choose_activity("Go Camping")
            if "Activity chosen: Go Camping" in result:
                assert state.chosen_activity == Activity.GO_CAMPING
        else:
            # If it's raining, camping should be blocked
            result = activity_plugin.choose_activity("Go Camping")
            assert "Rule violation" in result
    
    def test_swimming_happy_path(self):
        """Test complete swimming scenario - happy path."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        weather_plugin = next(p for p in plugins if hasattr(p, 'check_weather'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        
        # Step 1: Buy goggles
        result = shopping_plugin.shopping("Goggles")
        assert "Successfully purchased: Goggles" in result
        
        # Step 2: Check weather
        result = weather_plugin.check_weather()
        assert "Weather check complete" in result
        
        # Step 3: Go swimming (weather permitting)
        state = get_state()
        if state.weather != WeatherCondition.SNOWING:
            result = activity_plugin.choose_activity("Swimming")
            if "Activity chosen: Swimming" in result:
                assert state.chosen_activity == Activity.SWIMMING
        else:
            # If it's snowing, swimming should be blocked
            result = activity_plugin.choose_activity("Swimming")
            assert "Rule violation" in result
    
    def test_gaming_failure_missing_tv(self):
        """Test gaming scenario fails without TV."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        
        # Step 1: Buy only Xbox
        result = shopping_plugin.shopping("Xbox")
        assert "Successfully purchased: Xbox" in result
        
        # Step 2: Try to play games - should fail
        result = activity_plugin.choose_activity("Play games")
        assert "Rule violation" in result
        assert "TV" in result
        
        # Verify state
        state = get_state()
        assert state.chosen_activity is None
    
    def test_camping_failure_bad_weather(self):
        """Test camping scenario fails in bad weather."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        
        # Step 1: Buy hiking boots
        result = shopping_plugin.shopping("Hiking Boots")
        assert "Successfully purchased: Hiking Boots" in result
        
        # Step 2: Set rainy weather directly
        state = get_state()
        state.set_weather(WeatherCondition.RAINING)
        
        # Step 3: Try to go camping - should fail
        result = activity_plugin.choose_activity("Go Camping")
        assert "Rule violation" in result
        assert "raining" in result
        
        # Verify state
        assert state.chosen_activity is None
    
    def test_unknown_weather_restrictions(self):
        """Test that only gaming is allowed with unknown weather."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        
        # Prepare for activities
        shopping_plugin.shopping("TV")
        shopping_plugin.shopping("Xbox")
        shopping_plugin.shopping("Hiking Boots")
        shopping_plugin.shopping("Goggles")
        
        # Weather remains unknown
        state = get_state()
        assert state.weather == WeatherCondition.UNKNOWN
        
        # Gaming should work
        result = activity_plugin.choose_activity("Play games")
        assert "Activity chosen: Play games" in result
        
        # Reset activity for next test
        state.chosen_activity = None
        
        # Camping should be blocked
        result = activity_plugin.choose_activity("Go Camping")
        assert "Rule violation" in result
        assert "unknown" in result
        
        # Swimming should be blocked
        result = activity_plugin.choose_activity("Swimming")
        assert "Rule violation" in result
        assert "unknown" in result
    
    def test_weather_checking_restrictions(self):
        """Test weather can only be checked once."""
        plugins = get_plugins()
        weather_plugin = next(p for p in plugins if hasattr(p, 'check_weather'))
        
        # First check should work
        result = weather_plugin.check_weather()
        assert "Weather check complete" in result
        
        # Second check should be blocked
        result = weather_plugin.check_weather()
        assert "Rule violation" in result
        assert "already been checked" in result
    
    def test_multiple_activity_attempts(self):
        """Test trying multiple activities in sequence."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        weather_plugin = next(p for p in plugins if hasattr(p, 'check_weather'))
        
        # Buy all items
        shopping_plugin.shopping("TV")
        shopping_plugin.shopping("Xbox")
        shopping_plugin.shopping("Hiking Boots")
        shopping_plugin.shopping("Goggles")
        
        # Check weather
        weather_plugin.check_weather()
        
        state = get_state()
        
        # Try gaming first
        result = activity_plugin.choose_activity("Play games")
        assert "Activity chosen: Play games" in result
        assert state.chosen_activity == Activity.PLAY_GAMES
        
        # Try camping (should work if weather is good)
        if state.weather != WeatherCondition.RAINING:
            result = activity_plugin.choose_activity("Go Camping")
            if "Activity chosen: Go Camping" in result:
                assert state.chosen_activity == Activity.GO_CAMPING
        
        # Try swimming (should work if weather is good)
        if state.weather != WeatherCondition.SNOWING:
            result = activity_plugin.choose_activity("Swimming")
            if "Activity chosen: Swimming" in result:
                assert state.chosen_activity == Activity.SWIMMING


class TestStateConsistency:
    """Test state consistency across operations."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_state_persistence_across_plugins(self):
        """Test state persists across different plugin calls."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        state_plugin = next(p for p in plugins if hasattr(p, 'check_state'))
        
        # Initial state should be empty
        result = state_plugin.check_state()
        assert "Inventory: Empty" in result
        
        # Add item
        shopping_plugin.shopping("TV")
        
        # State should reflect the change
        result = state_plugin.check_state()
        assert "TV" in result
        assert "Inventory: Empty" not in result
    
    def test_state_consistency_after_multiple_operations(self):
        """Test state remains consistent after multiple operations."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        weather_plugin = next(p for p in plugins if hasattr(p, 'check_weather'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        
        # Perform multiple operations
        shopping_plugin.shopping("TV")
        shopping_plugin.shopping("Xbox")
        weather_plugin.check_weather()
        activity_plugin.choose_activity("Play games")
        
        # Verify final state is consistent
        state = get_state()
        assert "TV" in state.inventory
        assert "Xbox" in state.inventory
        assert state.weather_checked is True
        assert state.chosen_activity == Activity.PLAY_GAMES


class TestErrorRecovery:
    """Test system recovery from errors."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_invalid_operations_dont_break_state(self):
        """Test that invalid operations don't corrupt state."""
        plugins = get_plugins()
        shopping_plugin = next(p for p in plugins if hasattr(p, 'shopping'))
        activity_plugin = next(p for p in plugins if hasattr(p, 'choose_activity'))
        
        # Valid operation
        result = shopping_plugin.shopping("TV")
        assert "Successfully purchased: TV" in result
        
        # Invalid operation
        result = shopping_plugin.shopping("InvalidItem")
        assert "Invalid item" in result
        
        # State should still be consistent
        state = get_state()
        assert "TV" in state.inventory
        assert "InvalidItem" not in state.inventory
        
        # Valid operation should still work
        result = shopping_plugin.shopping("Xbox")
        assert "Successfully purchased: Xbox" in result