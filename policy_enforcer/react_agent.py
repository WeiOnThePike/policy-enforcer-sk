"""
ReAct Agent implementation for Semantic Kernel.

This module implements the ReAct (Reasoning + Acting) pattern using Semantic Kernel.
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.google.google_ai import GoogleAIChatCompletion, GoogleAIPromptExecutionSettings
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.functions import KernelArguments


class ReActStep(Enum):
    """ReAct processing steps."""
    THOUGHT = "Thought"
    ACTION = "Action"
    ACTION_INPUT = "Action Input"
    OBSERVATION = "Observation"
    FINAL_ANSWER = "Final Answer"


@dataclass
class ReActIteration:
    """Single iteration of the ReAct loop."""
    thought: str = ""
    action: str = ""
    action_input: Dict[str, Any] = None
    observation: str = ""
    
    def __post_init__(self):
        if self.action_input is None:
            self.action_input = {}


class ReActAgent:
    """
    ReAct (Reasoning + Acting) agent implementation for Semantic Kernel.
    
    This agent follows the ReAct pattern:
    1. Question: Input question to answer
    2. Thought: Reasoning about what to do
    3. Action: Tool/function to execute
    4. Action Input: Parameters for the tool
    5. Observation: Result of the action
    6. Repeat steps 2-5 until final answer is reached
    """
    
    def __init__(
        self,
        kernel: Kernel,
        service_id: str = "google_ai",
        name: str = "ReActAgent",
        instructions: str = "",
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        Initialize the ReAct agent.
        
        Args:
            kernel: Semantic Kernel instance with services and plugins
            service_id: ID of the AI service to use
            name: Name of the agent
            instructions: System instructions for the agent
            max_iterations: Maximum number of ReAct iterations
            verbose: Whether to print detailed execution logs
        """
        self.kernel = kernel
        self.service_id = service_id
        self.name = name
        self.instructions = instructions
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Get AI service settings
        self.settings = self._get_execution_settings()
        
        # Create chat completion agent for reasoning
        # Get the service from kernel
        service = kernel.get_service(service_id)
        
        self.reasoning_agent = ChatCompletionAgent(
            kernel=kernel,
            name=f"{name}_Reasoning",
            instructions=self._build_react_prompt(),
            service=service
            # Don't use function_choice_behavior - we parse text responses
        )
        
        # Chat history for conversation context
        self.chat_history = ChatHistory()
    
    def _get_execution_settings(self) -> GoogleAIPromptExecutionSettings:
        """Get execution settings for the AI service."""
        settings = GoogleAIPromptExecutionSettings()
        settings.max_output_tokens = 4000
        settings.temperature = 0.1
        # Don't use function calling - we'll parse the text response ourselves
        # settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        return settings
    
    def _build_react_prompt(self) -> str:
        """Build the ReAct prompt template."""
        # Get available functions from kernel
        functions = self.kernel.get_full_list_of_function_metadata()
        tool_descriptions = []
        tool_names = []
        
        for func_metadata in functions:
            if func_metadata.plugin_name and func_metadata.name:
                full_name = f"{func_metadata.plugin_name}.{func_metadata.name}"
                tool_names.append(full_name)
                tool_descriptions.append(f"{full_name}: {func_metadata.description}")
        
        tools_str = "\n".join(tool_descriptions)
        tool_names_str = ", ".join(tool_names)
        
        react_prompt = f"""
{self.instructions}

You are a ReAct (Reasoning + Acting) agent. You will receive a question and must answer it by reasoning through the problem step by step and taking actions when needed.

Available Tools:
{tools_str}

Tool Names: {tool_names_str}

You must follow this exact format for your responses:

IMPORTANT: Only output your thoughts and actions. Do NOT include observations - I will provide those after executing your actions.

Format:
Thought: [your reasoning about what to do next]
Action: [tool name to call, must be one of: {tool_names_str}]
Action Input: [JSON object with parameters for the tool]

OR if you have enough information:
Thought: [your reasoning]
Final Answer: [your complete answer to the question]

CRITICAL RULES:
1. NEVER write "Observation:" - I will provide that after executing your action
2. STOP after "Action Input:" and wait for me to give you the observation
3. Only use tools from the available list: {tool_names_str}
4. Action Input must be valid JSON
5. If you don't need tools, go directly to "Final Answer:"

Example:
Question: What is the weather like?
Thought: I need to check the current weather using the check_weather tool.
Action: weather.check_weather
Action Input: {{}}

[I will then provide the observation and you continue from there]

Begin!
"""
        return react_prompt
    
    async def run_async(self, question: str) -> str:
        """
        Run the ReAct agent asynchronously.
        
        Args:
            question: The question to answer
            
        Returns:
            The final answer from the agent
        """
        if self.verbose:
            print(f"\n🤖 {self.name} starting ReAct process...")
            print(f"❓ Question: {question}")
        
        # Reset chat history for new question
        self.chat_history = ChatHistory()
        
        # Add the question to start the ReAct process
        full_question = f"Question: {question}"
        if full_question.strip():  # Ensure content is not empty
            self.chat_history.add_user_message(full_question)
        
        iterations = []
        current_iteration = ReActIteration()
        
        for iteration_num in range(self.max_iterations):
            if self.verbose:
                print(f"\n🔄 Iteration {iteration_num + 1}/{self.max_iterations}")
            
            try:
                # Get the latest message to send
                if len(self.chat_history) > 0:
                    last_message = self.chat_history[-1]
                    message_content = last_message.content
                else:
                    message_content = full_question
                
                # Get response from reasoning agent with real-time streaming
                if self.verbose:
                    print("🧠 Agent thinking...", flush=True)
                
                response_stream = self.reasoning_agent.invoke(
                    messages=message_content
                )
                
                # Stream the response in real-time
                response_text = await self._stream_thinking_process(response_stream)
                
                # Parse the response to extract ReAct components
                final_answer = self._parse_response(response_text, current_iteration)
                
                if final_answer:
                    if self.verbose:
                        print(f"✅ Final Answer: {final_answer}")
                    return final_answer
                
                # Check if we have an action to execute
                has_action = current_iteration.action and current_iteration.action_input is not None
                
                if self.verbose:
                    print(f"\n🔍 Parsing result:")
                    print(f"   Action found: {current_iteration.action}")
                    print(f"   Action input: {current_iteration.action_input}")
                    print(f"   Will execute: {has_action}")
                
                if has_action:
                    if self.verbose:
                        print(f"\n🔄 Executing REAL tool: {current_iteration.action}...", flush=True)
                    
                    # Execute the action with real-time feedback
                    observation = await self._execute_action_with_feedback(
                        current_iteration.action,
                        current_iteration.action_input
                    )
                    current_iteration.observation = observation
                    
                    if self.verbose:
                        print(f"👀 REAL Observation from tool: {observation}")
                        print(f"\n{'='*50}")
                        print("🔄 Agent continuing to think...")
                        print(f"{'='*50}")
                    
                    # Add observation to chat history
                    self.chat_history.add_assistant_message(response_text)
                    self.chat_history.add_user_message(f"Observation: {observation}")
                    
                    # Save completed iteration and start new one
                    iterations.append(current_iteration)
                    current_iteration = ReActIteration()
                else:
                    # Add response to chat history for continuation
                    self.chat_history.add_assistant_message(response_text)
                    
                    if self.verbose:
                        print("\n⚠️ No action detected - agent may be hallucinating or providing final answer")
                
            except Exception as e:
                error_msg = f"Error in iteration {iteration_num + 1}: {str(e)}"
                if self.verbose:
                    print(f"❌ {error_msg}")
                return f"❌ {error_msg}"
        
        return "❌ Maximum iterations reached without finding a final answer."
    
    def run(self, question: str) -> str:
        """
        Run the ReAct agent synchronously.
        
        Args:
            question: The question to answer
            
        Returns:
            The final answer from the agent
        """
        return asyncio.run(self.run_async(question))
    
    def _parse_response(self, response: str, current_iteration: ReActIteration) -> Optional[str]:
        """
        Parse agent response to extract ReAct components.
        
        Args:
            response: Raw response from the agent
            current_iteration: Current iteration to populate
            
        Returns:
            Final answer if found, None otherwise
        """
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('Thought:'):
                current_iteration.thought = line[8:].strip()
            elif line.startswith('Action:'):
                current_iteration.action = line[7:].strip()
            elif line.startswith('Action Input:'):
                input_str = line[13:].strip()
                try:
                    current_iteration.action_input = json.loads(input_str) if input_str else {}
                except json.JSONDecodeError:
                    # If not valid JSON, treat as simple string
                    current_iteration.action_input = {"input": input_str}
            elif line.startswith('Final Answer:'):
                return line[13:].strip()
        
        return None
    
    async def _execute_action_with_feedback(self, action: str, action_input: Dict[str, Any]) -> str:
        """Execute action with real-time feedback display."""
        if self.verbose:
            print(f"\n📋 Preparing to call: {action}")
            print(f"📝 With parameters: {action_input}")
            
            # Show current state before action
            from .state import get_state
            state = get_state()
            print(f"📊 Current state before action:")
            print(f"   🎒 Inventory: {', '.join(sorted(state.inventory)) if state.inventory else 'Empty'}")
            print(f"   🌤️ Weather: {state.weather.value}")
            print(f"   🎯 Activity: {state.chosen_activity.value if state.chosen_activity else 'None'}")
            print()
        
        result = await self._execute_action(action, action_input)
        
        if self.verbose:
            print(f"✅ Action completed")
            
            # Show state changes after action
            state = get_state()
            print(f"📊 Updated state after action:")
            print(f"   🎒 Inventory: {', '.join(sorted(state.inventory)) if state.inventory else 'Empty'}")
            print(f"   🌤️ Weather: {state.weather.value}")
            print(f"   🎯 Activity: {state.chosen_activity.value if state.chosen_activity else 'None'}")
        
        return result
    
    async def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str:
        """
        Execute a tool action.
        
        Args:
            action: Name of the action/function to execute
            action_input: Parameters for the action
            
        Returns:
            Result of the action execution
        """
        try:
            # Parse plugin and function name
            if '.' in action:
                plugin_name, function_name = action.split('.', 1)
            else:
                # If no plugin specified, try to find the function
                plugin_name = None
                function_name = action
                
                # Search for the function in available plugins
                functions = self.kernel.get_functions_metadata()
                for func_metadata in functions:
                    if func_metadata.name == function_name:
                        plugin_name = func_metadata.plugin_name
                        break
            
            if not plugin_name:
                return f"❌ Could not find plugin for function: {action}"
            
            # Get the function from kernel
            function = self.kernel.get_function(plugin_name, function_name)
            if not function:
                return f"❌ Function not found: {action}"
            
            # Prepare arguments
            arguments = KernelArguments(**action_input)
            
            # Execute the function
            result = await function.invoke(self.kernel, arguments)
            
            return str(result.value) if result and result.value is not None else "✅ Action completed successfully"
            
        except Exception as e:
            return f"❌ Error executing action {action}: {str(e)}"
    
    async def _stream_thinking_process(self, response_stream):
        """Stream the agent's thinking process in real-time."""
        response_parts = []
        accumulated_content = ""
        
        async for item in response_stream:
            try:
                if hasattr(item, 'content'):
                    content = str(item.content) if item.content is not None else ""
                    response_parts.append(content)
                else:
                    content = str(item) if item is not None else ""
                    response_parts.append(content)
                
                if self.verbose and content:
                    accumulated_content += content  # Now guaranteed to be string
                    
                    # Process complete lines as they come in (real-time)
                    lines = accumulated_content.split('\n')
                    
                    # Process all complete lines except the last (potentially incomplete) one
                    for line in lines[:-1]:
                        if line.strip():
                            self._display_line_real_time(line.strip())
                    
                    # Keep the last potentially incomplete line for next iteration
                    accumulated_content = lines[-1] if lines else ""
                    
                    # Small delay for natural streaming effect
                    import asyncio
                    await asyncio.sleep(0.05)
                    
            except Exception as e:
                # Handle any unexpected content types gracefully
                content = f"[Error processing content: {str(e)}]"
                response_parts.append(content)
                if self.verbose:
                    print(f"⚠️ Warning: {content}", flush=True)
        
        # Process any remaining content
        if accumulated_content.strip():
            self._display_line_real_time(accumulated_content.strip())
        
        # Return the complete response (all parts are already strings now)
        complete_response = ''.join(response_parts)
        return complete_response
    
    def _display_line_real_time(self, line: str):
        """Display a line of thinking in real-time with appropriate formatting."""
        if not line:
            return
            
        if line.startswith('Thought:'):
            print(f"\n💭 {line}", flush=True)
        elif line.startswith('Action:'):
            print(f"⚡ {line}", flush=True)
        elif line.startswith('Action Input:'):
            print(f"📝 {line}", flush=True)
            print(f"🛑 Stopping LLM generation - about to execute tool...", flush=True)
        elif line.startswith('Final Answer:'):
            print(f"\n✅ {line}", flush=True)
        elif line.startswith('Question:'):
            print(f"\n❓ {line}", flush=True)
        elif line.startswith('Observation:'):
            # This should not appear in LLM output anymore, but handle it gracefully
            print(f"⚠️ LLM generated observation (should not happen): {line}", flush=True)
        else:
            # Print other content with indentation, but warn if it looks like hallucination
            if any(keyword in line.lower() for keyword in ['observation', 'result:', 'output:']):
                print(f"⚠️ Possible hallucination: {line}", flush=True)
            else:
                print(f"   {line}", flush=True)
    
    def reset(self):
        """Reset the agent's conversation history."""
        self.chat_history = ChatHistory()
        if self.verbose:
            print("🔄 ReAct agent conversation history reset.")