from enum import StrEnum
import json
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any, Optional, Type
from langchain_community.tools import BaseTool

def getContextRetrievalToolInput(employeeNames: List[str]) -> BaseModel:
    employeeNameEnum = StrEnum("EmployeeNameEnum", {name.replace(' ', '_').upper(): name for name in employeeNames})
    class ToolInput(BaseModel):
        employeeName: employeeNameEnum = Field(..., description="Name of the Assistant whose context is required. Even if there is some typo in the name or there is a different name, the function will try to find the most similar name from the list of Assistant names.")
    return ToolInput

class ContextRetrievalTool(BaseTool):
    name: str= "ContextRetrievalTool"
    description: str = "If the user query requires the context of any Assistant name, you can use this function to get the conversation summaries of the mentioned Assistant. The function takes a single parameter name."
    args_schema: Type[BaseModel] = None
    conversation_summary_mapping: Dict = {}

    def _run(self, employeeName: str) -> str:
        conversation_summary = {}                     
        if employeeName in self.conversation_summary_mapping:
            conversation_summary[employeeName] = f"Conversation summary with {employeeName} till now: \n\n{self.conversation_summary_mapping[employeeName]}"
        else:
            conversation_summary[employeeName] = f"No conversation summary available for {employeeName}."
        return json.dumps(conversation_summary)