"""Unit tests for rules module."""

import pytest
from policy_enforcer.rules import get_rule_engine, RuleEngine
from policy_enforcer.state import get_state, reset_state, WeatherCondition, Activity


class TestRuleEngine:
    """Test BusinessRuleEngine class."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_singleton_pattern(self):
        """Test rule engine follows singleton pattern."""
        engine1 = get_rule_engine()
        engine2 = get_rule_engine()
        assert engine1 is engine2
    
    def test_check_gaming_rules_success(self):
        """Test gaming rules when conditions are met."""
        state = get_state()
        state.add_to_inventory("TV")
        state.add_to_inventory("Xbox")
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.PLAY_GAMES.value)
        
        assert result.allowed is True
        assert result.reason is None  # No reason when allowed
    
    def test_check_gaming_rules_missing_tv(self):
        """Test gaming rules when TV is missing."""
        state = get_state()
        state.add_to_inventory("Xbox")
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.PLAY_GAMES.value)
        
        assert result.allowed is False
        assert "TV" in result.reason
    
    def test_check_gaming_rules_missing_xbox(self):
        """Test gaming rules when Xbox is missing."""
        state = get_state()
        state.add_to_inventory("TV")
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.PLAY_GAMES.value)
        
        assert result.allowed is False
        assert "Xbox" in result.reason
    
    def test_check_camping_rules_success(self):
        """Test camping rules when conditions are met."""
        state = get_state()
        state.add_to_inventory("Hiking Boots")
        state.set_weather(WeatherCondition.SUNNY)
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.GO_CAMPING.value)
        
        assert result.allowed is True
        assert result.reason is None  # No reason when allowed
    
    def test_check_camping_rules_missing_boots(self):
        """Test camping rules when hiking boots are missing."""
        state = get_state()
        state.set_weather(WeatherCondition.SUNNY)
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.GO_CAMPING.value)
        
        assert result.allowed is False
        assert "Hiking Boots" in result.reason
    
    def test_check_camping_rules_bad_weather(self):
        """Test camping rules when weather is raining."""
        state = get_state()
        state.add_to_inventory("Hiking Boots")
        state.set_weather(WeatherCondition.RAINING)
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.GO_CAMPING.value)
        
        assert result.allowed is False
        assert "raining" in result.reason
    
    def test_check_swimming_rules_success(self):
        """Test swimming rules when conditions are met."""
        state = get_state()
        state.add_to_inventory("Goggles")
        state.set_weather(WeatherCondition.SUNNY)
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.SWIMMING.value)
        
        assert result.allowed is True
        assert result.reason is None  # No reason when allowed
    
    def test_check_swimming_rules_missing_goggles(self):
        """Test swimming rules when goggles are missing."""
        state = get_state()
        state.set_weather(WeatherCondition.SUNNY)
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.SWIMMING.value)
        
        assert result.allowed is False
        assert "Goggles" in result.reason
    
    def test_check_swimming_rules_bad_weather(self):
        """Test swimming rules when weather is snowing."""
        state = get_state()
        state.add_to_inventory("Goggles")
        state.set_weather(WeatherCondition.SNOWING)
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.SWIMMING.value)
        
        assert result.allowed is False
        assert "snowing" in result.reason
    
    def test_unknown_weather_restriction(self):
        """Test that only gaming is allowed with unknown weather."""
        state = get_state()
        state.add_to_inventory("Hiking Boots")
        # Weather remains unknown
        
        engine = get_rule_engine()
        result = engine.check_activity_rules(state, Activity.GO_CAMPING.value)
        
        assert result.allowed is False
        assert "unknown" in result.reason
    
    def test_weather_tool_rules_success(self):
        """Test weather tool can be called when weather is unknown."""
        state = get_state()
        # Weather is unknown and not checked
        
        engine = get_rule_engine()
        result = engine.check_tool_rules(state, "check_weather")
        
        assert result.allowed is True
    
    def test_weather_tool_rules_already_checked(self):
        """Test weather tool cannot be called twice."""
        state = get_state()
        state.set_weather(WeatherCondition.SUNNY)  # This sets weather_checked = True
        
        engine = get_rule_engine()
        result = engine.check_tool_rules(state, "check_weather")
        
        assert result.allowed is False
        assert "already been checked" in result.reason
    
    def test_get_rules_summary(self):
        """Test getting rules summary."""
        engine = get_rule_engine()
        summary = engine.get_rules_summary()
        
        assert "Business Rules:" in summary
        assert "TV and an Xbox" in summary
        assert "Hiking Boots" in summary
        assert "Goggles" in summary
        assert "raining" in summary
        assert "snowing" in summary
        assert "unknown" in summary
    
    def test_unknown_activity(self):
        """Test handling of unknown activity with unknown weather."""
        state = get_state()
        engine = get_rule_engine()
        
        # Unknown activities are blocked when weather is unknown (only gaming allowed)
        result = engine.check_activity_rules(state, "Unknown Activity")
        assert result.allowed is False
        assert "unknown" in result.reason  # Weather restriction applies
        
        # But unknown activities should be allowed when weather is known
        state.set_weather(WeatherCondition.SUNNY)
        result = engine.check_activity_rules(state, "Unknown Activity")
        assert result.allowed is True