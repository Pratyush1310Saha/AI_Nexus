import os
from azure.identity import DefaultAzureCredential
from langchain_openai import AzureChatOpenAI
from Utilities.Config import app_config

def AzureChatModel(deployment_name = app_config.open_ai_deployment_name, 
                      endpoint = app_config.open_ai_endpoint, api_version = app_config.open_ai_api_version):
    if _AzureChatModel._instance is None or _AzureChatModel._instance["deployment_name"] != deployment_name or _AzureChatModel._instance["endpoint"] != endpoint or _AzureChatModel._instance["api_version"] != api_version:
        _AzureChatModel._instance = _AzureChatModel(deployment_name, endpoint, api_version).get_chat_model()
    return _AzureChatModel._instance["model"]

class _AzureChatModel:
    _instance = None
    def __init__(self, deployment_name = app_config.open_ai_deployment_name, 
                      endpoint = app_config.open_ai_endpoint, api_version = app_config.open_ai_api_version):
        self.deployment_name = deployment_name
        self.endpoint = endpoint
        self.api_version = api_version
        self.credential = DefaultAzureCredential()
        os.environ["OPENAI_API_TYPE"] = "azure_ad"
        # Set the API_KEY to the token from the Azure credential
        self.credential.get_token("https://cognitiveservices.azure.com/.default").token
        os.environ["AZURE_OPENAI_ENDPOINT"] = self.endpoint
        os.environ["OPENAI_API_VERSION"] = self.api_version
        
    def get_chat_model(self):
        model = AzureChatOpenAI(
            azure_deployment=self.deployment_name,
            temperature=0,
            azure_ad_token_provider = lambda : self.credential.get_token("https://cognitiveservices.azure.com/.default").token
        )
        chat_model_dict = {
            'model': model,
            'deployment_name': self.deployment_name,
            'endpoint': self.endpoint,
            'api_version': self.api_version,
        }
        return chat_model_dict