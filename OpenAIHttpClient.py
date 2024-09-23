from datetime import datetime
from math import e
import trace
import requests
import threading
import time
from azure.identity import AzureCliCredential
import json
import inspect
from pathlib import Path

def OpenAIHttpClient(logger = None):
    if _OpenAIHttpClient._instance is None:
        _OpenAIHttpClient._instance = _OpenAIHttpClient(logger = logger)
    return _OpenAIHttpClient._instance

class _OpenAIHttpClient():
    _instance = None
    
    def __init__(self, logger = None) -> None:
        self.headers = {}
        self.headers["Content-Type"] = "application/json"
        self.aad_token_expiry = 0
        self.resetAccessToken(force = True)
        self.url = "https://DataScienceOpenAIEastUS-2.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2023-03-15-preview"
    
    def getToken(self, audience):
        credential = AzureCliCredential()
        token = credential.get_token(audience)
        return token    
        
    def resetAccessToken(self, force = False):
        if ((force) or (time.time() > self.aad_token_expiry)):
            self.aad_token = self.getToken("https://cognitiveservices.azure.com/.default")
            self.aad_token_expiry = self.aad_token.expires_on
            self.headers["Authorization"] = f"Bearer {self.aad_token.token}"
        

    def getChatCompletionResponse(self, messages, max_tokens = 1000, stop = None, temperature = 0,
                                  top_p = 0.9, resource = None, deploymentId = None, traceObj = None, stream = False, employee_names = []):
       
        self.resetAccessToken()
        image_generator_function_definition = {
            "name": "generate_image",
            "strict": True,
            "description": "If you want to generate an image based on the user query, you can use this function. The function takes a single parameter 'prompt' based on which the image is to be generated.",
            "parameters": {
                "type": "object",
                "properties":{
                    "prompt": {
                        "type": "string",
                        "description": "The prompt based on which the image is to be generated."
                    }
                },
                "required": ["prompt"],
                "additionalProperties": False
            }
        }
        
        get_employee_conversation_summary_definition = {
            "name": "get_employee_conversation_summary",
            "strict": True,
            "description": "If the user query requires the context of any employee name, you can use this function to get the conversation summaries of the mentioned employee. The function takes a single parameter name.",
            "parameters": {
                "type": "object",
                "properties":{
                    "name": {
                        "type": "string",
                        "description": "Employee name about whom the conversation summary (context) is required to answer the current user query.",
                        "enum": employee_names
                    }
                },
                "required": ["name"],
                "additionalProperties": False
            }
        }
        
        data = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": stop,
            "stream": stream,
            "tools" :[
                {
                    "type": "function",
                    "function": image_generator_function_definition
                },
                {
                    "type": "function",
                    "function": get_employee_conversation_summary_definition
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "strict": True,
                    "schema":{
                        "type": "object",
                        "properties":{
                            "answer":
                            {
                                "type": "string",
                                "description": "The answer to the current user query based on the previous messages exchanged between the user and the assistant."
                            },
                            "summary":
                            {
                                "type": "string",
                                "description": "A comprehensive yet to the point summary reported in third person of what has been accomplished till now in the conversation, including the last user query, the answer provided by the assistant and all the previously exchanged messages."
                            }
                        },
                        "required": ["answer", "summary"],
                        "additionalProperties": False
                        
                    }
                }
            }
        }
        try:
            response = requests.post(url=self.url, json=data, headers=self.headers, stream = stream)
            response = response.json()
            return response
        except:
            print("Ran into an error while using OpenAI Completion API")
            print(f'content {response}')
            raise       
