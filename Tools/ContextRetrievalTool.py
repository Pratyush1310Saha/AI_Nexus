from enum import StrEnum
import json
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any, Optional, Type
from langchain_community.tools import BaseTool

def getContextRetrievalToolInput(employeeNames: List[str]) -> BaseModel:
    employeeNameEnum = StrEnum("EmployeeNameEnum", {name.replace(' ', '_').upper(): name for name in employeeNames})
    class ToolInput(BaseModel):
        employeeNames: employeeNameEnum = Field(..., description="Name of the employee whose context is required.")
    return ToolInput

class ContextRetrievalTool(BaseTool):
    name: str= "ContextRetrievalTool"
    description: str = "If the user query requires the context of any employee name, you can use this function to get the conversation summaries of the mentioned employee. The function takes a single parameter name."
    args_schema: Type[BaseModel] = None
    session_state: Any = None

    def _run(self, employeeName: str) -> str:
        conversation_summary = {}                     
        employee_id = self.session_state['node_name_to_id'][employeeName]
        if employee_id in self.session_state['conversation_summary']:
            conversation_summary[employeeName] = f"Conversation summary with {employeeName} till now: \n\n{self.session_state['conversation_summary'][employee_id]}"
        else:
            conversation_summary[employeeName] = f"No conversation summary available for {employeeName}."
        return json.dumps(conversation_summary)