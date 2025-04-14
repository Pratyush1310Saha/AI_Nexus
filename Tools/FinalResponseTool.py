from pydantic import BaseModel, Field
from typing import Optional, List

last_N = 10  # Number of last messages to include in the summary
class FinalResponse(BaseModel):
    """When all the necessary information is gathered, this function is called to generate the final response."""
    response: str = Field(..., description = "The answer to the current user query based on the previous messages exchanged between the user and the assistant.")
    summary: str = Field(..., description = f"A comprehensive yet to the point summary, containing all the key details and important discussion points, reported in third person of what has been accomplished till now in the conversation, including the last user query, the answer provided by the assistant and the last {last_N} previously exchanged messages.")