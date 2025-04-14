
```markdown
# Core

This folder contains core components that drive the AI Nexus application's orchestration logic.

## Components

### Orchestrator.py
The central orchestration system that:
- Creates and manages LangGraph-based agent workflows
- Handles tool selection and execution
- Manages conversation state and agent responses
- Implements error handling and fallback mechanisms

### EventEnums.py
Contains enumerations for different event types processed by the system:
- Tool start/end events
- Chat model streaming events
- Agent state transition events
- Error and completion events

### AppMessages.py
Contains predefined message templates for:
- Fallback responses when errors occur
- System prompts for different agent roles
- Instructional messages for users
- Status messages for UI feedback

## Usage

The core components are typically used to create and run conversational agents