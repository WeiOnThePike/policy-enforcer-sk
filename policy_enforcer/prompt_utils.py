"""
Prompt utilities for the Policy Enforcer.

This module provides prompt generation for Semantic Kernel agents.
"""

from .rules import get_rule_engine


def generate_prompt_instructions(include_rules: bool = True) -> str:
    """
    Generate instructions for the ReAct agent.
    
    Args:
        include_rules: Whether to include business rules in the instructions
        
    Returns:
        Complete instructions string for the agent
    """
    rule_engine = get_rule_engine()
    
    if include_rules:
        rules_section = f"""
IMPORTANT: You must follow these business rules at all times:

{rule_engine.get_rules_summary()}"""
        
        instructions_section = """
CRITICAL: STATE AWARENESS INSTRUCTIONS:
- After EVERY tool call that changes state (shopping, weather check, activity choice), the tool output will show you the updated state
- PAY ATTENTION to the "📊 Current inventory:" and "📊 Weather status:" information in tool outputs
- If you're unsure about the current state, use the "check_state" tool to get the latest information
- The state persists across your actions - if you buy an item, it stays in inventory
- Always consider the CURRENT state when making decisions, not just the initial state

Instructions:
1. ALWAYS pay attention to state changes reported in tool outputs. Latest state and tool outputs will be provided after each action.
2. Use "check_state" tool if you need to verify current inventory, weather, or activity
3. If a user asks to do something that violates business rules, explain why it's not allowed and suggest alternatives
4. Help users gather required items or check weather as needed
5. Be helpful and guide users through the process step by step
6. If rules prevent an action, explain the specific rule and what needs to be done to satisfy it
7. Remember that your actions have persistent effects - purchased items stay in inventory"""
    else:
        rules_section = """
IMPORTANT: Business rules are enforced automatically during tool execution. You are not given the specific rules upfront, but you should:
- Pay close attention to tool execution results
- If a tool call fails due to a rule violation, the error message will explain what went wrong
- Learn from these failures and adapt your approach accordingly
- Use failed attempts to infer the underlying business constraints
- Suggest alternative actions when rules block your initial approach"""
        
        instructions_section = """
CRITICAL: STATE AWARENESS INSTRUCTIONS:
- After EVERY tool call that changes state (shopping, weather check, activity choice), the tool output will show you the updated state
- PAY ATTENTION to the "📊 Current inventory:" and "📊 Weather status:" information in tool outputs
- If you're unsure about the current state, use the "check_state" tool to get the latest information
- The state persists across your actions - if you buy an item, it stays in inventory
- Always consider the CURRENT state when making decisions, not just the initial state

Instructions:
1. ALWAYS pay attention to state changes reported in tool outputs. Latest state and tool outputs will be provided after each action.
2. Use "check_state" tool if you need to verify current inventory, weather, or activity
3. When tool calls fail due to rule violations, carefully read the error messages to understand the constraints
4. Adapt your strategy based on rule violation feedback and suggest compliant alternatives
5. Help users gather required items or check weather as needed
6. Be helpful and guide users through the process step by step, learning from any failures
7. Remember that your actions have persistent effects - purchased items stay in inventory
8. Use trial and observation to infer business rules when they're not explicitly provided"""
    
    full_instructions = f"""
You are a helpful assistant that helps users choose activities. You have access to tools that allow you to check weather, shop for items, choose activities, and check current state.
{rules_section}

{instructions_section}

Available activities: Play games, Go Camping, Swimming

You should be conversational, helpful, and guide users toward successful completion of their goals while respecting all business constraints.
"""
    
    return full_instructions