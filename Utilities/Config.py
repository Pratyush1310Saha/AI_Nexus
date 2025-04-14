from enum import StrEnum

class app_config(StrEnum):
    open_ai_deployment_name = "gpt-4o"
    open_ai_api_version = "2024-10-01-preview"
    open_ai_endpoint = "https://DataScienceOpenAIEastUS-2.openai.azure.com/"
    image_generation_deployment_name = "Dalle3"