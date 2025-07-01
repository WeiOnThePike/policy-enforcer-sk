#!/usr/bin/env python3
"""
Policy Enforcer CLI - Semantic Kernel ReAct Agent Demo with Business Rule Enforcement
"""

import argparse
import os
import sys
from typing import Optional
from dotenv import load_dotenv

from policy_enforcer.agents import create_agent
from policy_enforcer.state import get_state, reset_state
from policy_enforcer.rules import get_rule_engine


def print_banner(include_rules_mode: bool = True):
    """Print the application banner."""
    mode_text = "WITH Business Rules" if include_rules_mode else "WITHOUT Business Rules (Learning Mode)"
    banner = f"""
╔═══════════════════════════════════════════════════════════╗
║                    Policy Enforcer Demo                   ║
║              ReAct Agent {mode_text:<20} ║
║                   Powered by OpenAI                       ║
╚═══════════════════════════════════════════════════════════╝

This demo showcases a ReAct agent that enforces business rules
when helping users choose activities.

Available activities: Play games, Go Camping, Swimming
Type 'help' for available commands.
"""
    print(banner)


def print_help(include_rules_mode: bool = True):
    """Print help information."""
    mode_desc = "explicit rules" if include_rules_mode else "learning mode (no upfront rules)"
    help_text = f"""
Available Commands:
  help              - Show this help message
  rules             - Show current business rules
  state             - Show current agent state
  reset             - Reset agent state
  quit/exit         - Exit the application
  
  Or simply type your request to interact with the agent!
  
🔬 Ablation Study Mode: Agent running in {mode_desc}
  
Examples:
  "I want to go camping"
  "Check the weather"
  "Buy hiking boots"
  "What activities can I do?"
"""
    print(help_text)


def setup_environment() -> bool:
    """Setup environment variables and check requirements."""
    # Load environment variables from .env file in the project root
    load_dotenv()
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set your OpenAI API key in a .env file or environment variable.")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    print(f"✅ OpenAI API key loaded successfully (length: {len(api_key)} chars)")
    return True


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Policy Enforcer CLI - Semantic Kernel ReAct Agent Demo with Business Rule Enforcement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ablation Study Modes:
  --rules (default)     Agent receives explicit business rules in prompt
  --no-rules           Agent learns rules through tool execution feedback

Examples:
  python main.py                    # Standard mode with rules
  python main.py --no-rules         # Learning mode without upfront rules
  python main.py --rules            # Explicitly enable rules mode
        """
    )
    
    # Ablation study toggle
    rules_group = parser.add_mutually_exclusive_group()
    rules_group.add_argument(
        '--rules',
        action='store_true',
        default=True,
        help='Include business rules in agent prompt (default)'
    )
    rules_group.add_argument(
        '--no-rules',
        action='store_true',
        help='Run agent without upfront rules (learning mode for ablation study)'
    )
    
    # Temperature control
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='Model temperature (0.0-1.0, default: 0.1)'
    )
    
    # Model selection
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4o-mini',
        help='Model name (default: gpt-4o-mini)'
    )
    
    return parser.parse_args()


def main():
    """Main CLI application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine include_rules_in_prompt setting
    include_rules_in_prompt = not args.no_rules
    
    print_banner(include_rules_in_prompt)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Create agent
    print("🚀 Initializing ReAct agent...")
    try:
        agent = create_agent(
            model_name=args.model,
            temperature=args.temperature,
            include_rules_in_prompt=include_rules_in_prompt
        )
        mode_status = "WITH explicit rules" if include_rules_in_prompt else "WITHOUT upfront rules (learning mode)"
        print(f"✅ Agent initialized successfully in {mode_status}!")
        
        if not include_rules_in_prompt:
            print("🔬 Ablation Study: Agent will learn rules through tool execution feedback")
        
        print()
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Main interaction loop
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'help':
                print_help(include_rules_in_prompt)
                continue
            elif user_input.lower() == 'rules':
                print("📜 " + agent.show_rules())
                continue
            elif user_input.lower() == 'state':
                print(agent.show_state())
                continue
            elif user_input.lower() == 'reset':
                agent.reset()
                continue
            
            # Process user input with agent
            print("🤖 Agent: Thinking...")
            response = agent.run(user_input)
            print(f"🤖 Agent: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Type 'help' for available commands.")


if __name__ == "__main__":
    main()