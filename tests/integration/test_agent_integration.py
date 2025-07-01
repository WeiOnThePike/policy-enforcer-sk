"""Integration tests for agent functionality."""

import pytest
from unittest.mock import patch, MagicMock
import os

from policy_enforcer.agents import create_agent, PolicyEnforcerAgent
from policy_enforcer.state import get_state, reset_state, WeatherCondition, Activity


class TestAgentCreation:
    """Test agent creation and initialization."""
    
    def test_create_agent_without_api_key(self):
        """Test agent creation fails without API key."""
        # Ensure no API key is set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                create_agent()
    
    def test_create_agent_with_api_key(self):
        """Test agent creation succeeds with API key."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent()
            assert isinstance(agent, PolicyEnforcerAgent)
            assert agent.model_name == "gpt-4o-mini"
            assert agent.temperature == 0.1
    
    def test_create_agent_custom_parameters(self):
        """Test agent creation with custom parameters."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent(
                model_name="gpt-4",
                temperature=0.5,
                include_rules_in_prompt=False
            )
            assert agent.model_name == "gpt-4"
            assert agent.temperature == 0.5
            assert agent.include_rules_in_prompt is False


@pytest.mark.requires_api
class TestAgentBasicOperations:
    """Test basic agent operations."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_agent_reset(self):
        """Test agent reset functionality."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent()
            
            # Modify state
            state = get_state()
            state.add_to_inventory("TV")
            state.set_weather(WeatherCondition.SUNNY)
            
            # Reset agent
            agent.reset()
            
            # Verify state is reset
            state = get_state()
            assert len(state.inventory) == 0
            assert state.weather == WeatherCondition.UNKNOWN
            assert state.weather_checked is False
    
    def test_agent_show_state(self):
        """Test agent show state functionality."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent()
            
            state_info = agent.show_state()
            assert "Current State:" in state_info
            assert "Inventory" in state_info
            assert "Weather" in state_info
    
    def test_agent_show_rules(self):
        """Test agent show rules functionality."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent()
            
            rules_info = agent.show_rules()
            assert "Business Rules:" in rules_info
            assert "TV and an Xbox" in rules_info
            assert "Hiking Boots" in rules_info


class TestAgentScenarios:
    """Test complete agent scenarios."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    @pytest.mark.slow
    def test_gaming_scenario_mock(self):
        """Test gaming scenario with mocked AI responses."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent()
            
            # Mock the ReAct agent to simulate AI responses
            with patch.object(agent.react_agent, 'run') as mock_run:
                mock_run.return_value = "I need to buy a TV and Xbox first, then I can play games."
                
                result = agent.run("I want to play games")
                assert "TV" in result or "Xbox" in result
    
    @pytest.mark.slow  
    def test_camping_scenario_mock(self):
        """Test camping scenario with mocked AI responses."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent()
            
            # Mock the ReAct agent to simulate AI responses
            with patch.object(agent.react_agent, 'run') as mock_run:
                mock_run.return_value = "I need hiking boots and to check the weather before camping."
                
                result = agent.run("I want to go camping")
                assert "hiking boots" in result.lower() or "weather" in result.lower()


class TestAgentRuleEnforcement:
    """Test agent rule enforcement in integration."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_state()
    
    def test_agent_enforces_gaming_rules(self):
        """Test agent enforces gaming rules through plugins."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent()
            
            # Get plugins and test rule enforcement directly
            plugins = agent.react_agent.kernel.get_plugin("activity")
            if plugins:
                # Test that activity plugin enforces rules
                state = get_state()
                
                # Try to play games without items - should fail
                result = plugins.choose_activity("Play games")
                assert "Rule violation" in result
                
                # Add required items
                state.add_to_inventory("TV")
                state.add_to_inventory("Xbox")
                
                # Try again - should succeed
                result = plugins.choose_activity("Play games")
                assert "Activity chosen" in result


class TestAgentConfiguration:
    """Test different agent configurations."""
    
    def test_agent_with_rules_in_prompt(self):
        """Test agent configuration with rules in prompt."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent(include_rules_in_prompt=True)
            assert agent.include_rules_in_prompt is True
            
            # Rules should be included in instructions
            instructions = agent.react_agent.instructions
            assert "Business Rules" in instructions or "rules" in instructions.lower()
    
    def test_agent_without_rules_in_prompt(self):
        """Test agent configuration without rules in prompt."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent(include_rules_in_prompt=False)
            assert agent.include_rules_in_prompt is False
            
            # Rules should not be explicitly stated in instructions
            instructions = agent.react_agent.instructions
            # Agent should learn through tool feedback instead


class TestAgentErrorHandling:
    """Test agent error handling."""
    
    def test_agent_handles_invalid_api_key(self):
        """Test agent handles invalid API key gracefully."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'invalid-key'}):
            agent = create_agent()
            
            # Mock a network error response
            with patch.object(agent.react_agent, 'run') as mock_run:
                mock_run.side_effect = Exception("API key invalid")
                
                result = agent.run("test input")
                assert "Error" in result
    
    def test_agent_handles_empty_input(self):
        """Test agent handles empty input gracefully."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = create_agent()
            
            result = agent.run("")
            # Should handle empty input without crashing
            assert isinstance(result, str)