# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Core Testing Commands
```bash
# Test plugin functionality
python test_plugins.py
```

### Running the Application
```bash
# Full agent (requires Google API key)
python main.py

# Demo mode (no API key required)
python demo.py

# Ablation study modes
python main.py --rules        # With explicit rules (default)
python main.py --no-rules     # Learning mode without upfront rules
```

### Dependency Management
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Semantic Kernel dependencies
pip install -r requirements.txt

# Install development dependencies (includes testing tools)
pip install -r requirements-dev.txt
```

## Architecture Overview

### Migration to Semantic Kernel
This codebase has been **migrated from LangChain to Semantic Kernel** while preserving the core policy enforcement pattern. Both implementations coexist for comparison.

### Core Design Pattern: Policy-Enforced Tools
This codebase demonstrates **Constrained Autonomy** - letting ReAct agents think freely while enforcing business constraints at execution time. The key architectural components are:

**Semantic Kernel Implementation (NEW):**
1. **Custom ReAct Agent** (`policy_enforcer/react_agent.py`): Custom ReAct implementation since SK doesn't have built-in ReAct
2. **PolicyEnforcedPlugin Base Class** (`policy_enforcer/sk_tools.py`): Plugin-based tools with automatic rule checking
3. **Semantic Kernel Functions**: Using `@kernel_function` decorators for tool registration
4. **PolicyEnforcerSKAgent** (`policy_enforcer/sk_agents.py`): Main agent wrapper for Semantic Kernel

**Original LangChain Implementation:**
1. **PolicyEnforcedTool Base Class** (`policy_enforcer/tools/__init__.py:76`): All tools automatically check business rules before execution
2. **RuleEngine** (`policy_enforcer/rules/__init__.py:202`): Centralized rule evaluation with explainable violations
3. **AgentState** (`policy_enforcer/state/__init__.py:25`): Persistent state tracking across tool executions
4. **Separation of Concerns**: Business rules are completely separate from agent reasoning logic

### State Management
- **Global State**: Single `agent_state` instance tracks inventory, weather, activity choices
- **State Updates**: Tools automatically update state during execution
- **State Persistence**: State persists across agent interactions until explicitly reset

### Business Rules Engine
- **Abstract BusinessRule Class**: All rules inherit from common interface
- **Rule Categories**: Equipment rules, weather rules, tool usage rules
- **Explainable Failures**: Rules return detailed reasons when violated
- **Rule Engine**: Evaluates rules by category (activity rules vs tool rules)

### Tools Architecture

**Semantic Kernel Implementation:**
- Plugins inherit from `PolicyEnforcedPlugin` base class
- Functions use `@kernel_function` decorators with type annotations
- **WeatherPlugin**: Sets random weather, enforces single-check rule
- **ShoppingPlugin**: Adds items to inventory with validation  
- **ActivityPlugin**: Validates activities against all business rules
- **StatePlugin**: Shows current state without modification

**Original LangChain Implementation:**
All tools inherit from `PolicyEnforcedTool`:
- `CheckWeatherTool`: Sets random weather, enforces single-check rule
- `ShoppingTool`: Adds items to inventory with validation
- `ChooseActivityTool`: Validates activities against all business rules
- `CheckStateTool`: Shows current state without modification

### Agent Architecture

**Semantic Kernel Implementation:**
- **Custom ReAct Agent**: Manual implementation of ReAct pattern (`policy_enforcer/react_agent.py`)
- **Google AI Integration**: Uses Google's Gemini models via Semantic Kernel connectors
- **Plugin System**: Automatic function registration and discovery
- **State-Aware Prompting**: Current state automatically included in agent context

**Original LangChain Implementation:**
- **ReAct Agent**: Uses LangChain's `create_react_agent` with Gemini 1.5 Flash
- **Prompt Modes**: Can run with explicit rules or in learning mode for ablation studies
- **State-Aware Prompting**: Current state is automatically included in agent context

## Key Implementation Details

### Rule Enforcement Pattern
Rules are checked in `PolicyEnforcedTool._run()` method before actual tool execution:
```python
def _run(self, tool_input: Optional[str] = None, **kwargs) -> str:
    params = self.parse_input(tool_input)
    rule_violation = self.check_tool_rules(**params)
    if rule_violation:
        return f"❌ Rule violation: {rule_violation}"
    return self.execute(**params)
```

### LangChain Integration Workaround
The codebase includes a workaround for LangChain's JSON parameter mapping issues in `parse_langchain_input()` function.

### Ablation Study Support
The system supports two modes for research:
- **Explicit Rules Mode**: Business rules included in agent prompt
- **Learning Mode**: Agent learns rules through tool execution feedback

### Testing Strategy
- 101+ unit tests with 86% coverage
- Test categories: unit tests, integration tests, error handling
- Comprehensive rule validation testing
- LangChain tool integration testing

## File Structure Highlights

**New Semantic Kernel Files:**
- `main_sk.py`: Semantic Kernel CLI entry point
- `policy_enforcer/react_agent.py`: Custom ReAct agent implementation for Semantic Kernel
- `policy_enforcer/sk_agents.py`: Semantic Kernel agent wrapper
- `policy_enforcer/sk_tools.py`: Semantic Kernel plugins with policy enforcement
- `policy_enforcer/sk_prompt_utils.py`: Prompt generation for Semantic Kernel
- `test_sk_migration.py`: Migration validation tests

**Original LangChain Files:**
- `main.py`: CLI entry point with argument parsing and environment setup
- `demo.py`: API-key-free demonstration of rule engine
- `policy_enforcer/agents/`: ReAct agent implementation with custom prompting
- `policy_enforcer/rules/`: Complete business rules engine with 7 specific rules
- `policy_enforcer/state/`: Pydantic-based state management with persistence
- `policy_enforcer/tools/`: Policy-enforced LangChain tools
- `policy_enforcer/items.py`: Item definitions and activity requirements
- `policy_enforcer/prompt_utils.py`: Centralized prompt generation for ablation studies

## Key Differences: LangChain vs Semantic Kernel

### ReAct Implementation
- **LangChain**: Built-in `create_react_agent` function with AgentExecutor
- **Semantic Kernel**: Custom implementation required (`policy_enforcer/react_agent.py`)

### Tool/Function Definition
- **LangChain**: Class-based tools inheriting from `BaseTool`
- **Semantic Kernel**: Plugin classes with `@kernel_function` decorated methods

### Function Calling
- **LangChain**: Automatic with `handle_parsing_errors=True`
- **Semantic Kernel**: Manual orchestration in custom ReAct loop

### Model Integration
- **LangChain**: `ChatGoogleGenerativeAI` with `langchain-google-genai`
- **Semantic Kernel**: `GoogleAIChatCompletion` with built-in Google AI connector

### Configuration
- **LangChain**: Prompt templates with variable substitution
- **Semantic Kernel**: Direct instruction strings with function metadata

### Error Handling
- **LangChain**: Built-in parsing error recovery
- **Semantic Kernel**: Manual error handling in ReAct loop

## Development Notes

### Environment Setup
- Requires Google API key in environment variable `GOOGLE_API_KEY`
- Uses `python-dotenv` for environment variable loading
- No `.env.example` file exists - create one if needed

### Testing Framework
- Uses pytest with custom markers: `integration`, `unit`, `error_handling`
- Coverage reporting via pytest-cov
- All tests designed to run independently without external dependencies

### Model Configuration
- Default: Gemini 1.5 Flash with temperature 0.1
- Configurable via command line arguments
- Supports any Google Generative AI model

This codebase serves as a production-ready foundation for building enterprise AI agents that balance autonomy with business compliance.