
```markdown
# Utilities

This folder contains utility classes and helper functions used throughout the AI Nexus application.

## Files

### AzureChatModel.py
Contains the implementation of the Azure OpenAI chat model client. This class handles:
- Authentication with Azure AD
- Creation and management of chat model instances
- Token management and renewal

### AzureImageGenerator.py
Provides functionality to generate images using Azure's DALL-E API:
- Handles authentication similar to the chat model
- Provides methods to generate images from text prompts
- Manages API responses and error handling

### Config.py
Contains application configuration including:
- API endpoints
- Deployment names
- API versions
- Other application-wide settings

### HelperFunctions.py
Collection of helper functions for:
- Message formatting for chat models
- Stream handling for real-time responses
- Content extraction and parsing utilities

## Usage

These utilities are designed to be imported and used by other components of the application