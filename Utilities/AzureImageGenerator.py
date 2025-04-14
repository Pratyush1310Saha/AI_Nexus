import os
import requests
import time
from azure.identity import DefaultAzureCredential
from Utilities.Config import app_config

def AzureImageGenerator(deployment_name = app_config.image_generation_deployment_name,
                      endpoint = app_config.open_ai_endpoint, api_version = "2024-02-01"):
    if _AzureImageGenerator._instance is None or _AzureImageGenerator._instance["deployment_name"] != deployment_name or _AzureImageGenerator._instance["endpoint"] != endpoint or _AzureImageGenerator._instance["api_version"] != api_version:
        _AzureImageGenerator._instance = _AzureImageGenerator(deployment_name, endpoint, api_version)
    return _AzureImageGenerator._instance

class _AzureImageGenerator:
    _instance = None
    
    def __init__(self, deployment_name = app_config.image_generation_deployment_name,
                endpoint = app_config.open_ai_endpoint, api_version = "2024-02-01"):
        self.deployment_name = deployment_name
        self.endpoint = endpoint
        self.api_version = api_version
        self.credential = DefaultAzureCredential()
        self.headers = {
            "Content-Type": "application/json"
        }
        self.token_expiry = 0
        self.reset_access_token(force=True)
        
    def reset_access_token(self, force=False):
        """Reset the access token if it's expired or force is True"""
        if force or time.time() > self.token_expiry:
            token = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            self.headers["Authorization"] = f"Bearer {token.token}"
            self.token_expiry = token.expires_on
    
    def generate_image(self, prompt, size="1024x1024", n=1):
        """Generate an image using the DALL-E API"""
        self.reset_access_token()
        
        url = f"{self.endpoint}openai/deployments/{self.deployment_name}/images/generations?api-version={self.api_version}"
        
        payload = {
            "prompt": prompt,
            "n": n,
            "size": size
        }
        
        try:
            response = requests.post(url=url, json=payload, headers=self.headers)
            result = response.json()
            
            if "data" in result and len(result["data"]) > 0:
                return result["data"][0]["url"]
            else:
                return None
        except Exception as e:
            print(f"Error generating image: {e}")
            return "Sorry, unable to generate image at this time. Please try again later."