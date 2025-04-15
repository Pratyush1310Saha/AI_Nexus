
```markdown
# Tools

This folder contains specialized tools used by the AI agents in the AI Nexus application.

## Tool Components

### ContextRetrievalTool.py
Implements a tool for retrieving conversation context:
- Retrieves historical conversation summaries
- Allows AI agents to access context from different Assistant conversations
- Enables more coherent cross-conversation interactions

### ImageGenerationTool.py
Implements image generation capabilities:
- Connects to Azure DALL-E API to generate images from text prompts
- Handles the conversion of text descriptions to visual content
- Returns URLs to generated images that can be displayed in the chat

### FinalResponseTool.py
Handles the final response formatting:
- Structures agent responses in a consistent format
- Generates conversation summaries
- Ensures responses meet the application's formatting requirements

## Tool Structure

Each tool follows a similar structure using the LangChain BaseTool pattern:
- Input schema definition using Pydantic models
- Tool description and metadata for agent discovery
- Implementation of _run method with the core tool functionality
- Optional additional methods like status_message for UI feedback

## Usage

Tools are primarily used by the LangGraph orchestrator but can also be used directly:

```python
from Tools.ImageGenerationTool import ImageGenerationTool

# Create an instance of the tool
image_tool = ImageGenerationTool()

# Use the tool
image_url = image_tool._run(prompt="A serene mountain landscape at sunset")