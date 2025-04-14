from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any, Optional, Type
from langchain_community.tools import BaseTool

from Utilities.AzureImageGenerator import AzureImageGenerator, _AzureImageGenerator
from Core.AppMessages import FallbackMessages

class _ImageGenerationToolInput(BaseModel):
    prompt: str = Field(description="The prompt based on which the image is to be generated.")
    size: Optional[str] = Field(default="1024x1024", description="The size of the image to be generated.")
    n: Optional[int] = Field(default=1, description="The number of images to be generated.")
    
class ImageGenerationTool(BaseTool):
    """Tool to generate images using DALL-E API. It returns the URL of the generated image."""    
    name: str = "ImageGenerationTool"
    description: str = "If you want to generate an image based on the user query, you can use this function. The function takes a single parameter 'prompt' based on which the image is to be generated."
    args_schema: Type[_ImageGenerationToolInput] = _ImageGenerationToolInput
    image_generator: _AzureImageGenerator = AzureImageGenerator()
    status_message: str = "Generating image..."
    
    def _run(self, prompt: str, size: Optional[str] = "1024x1024", n: Optional[int] = 1) -> str:
        """Generate an image using the DALL-E API."""
        try:
            image_url = self.image_generator.generate_image(prompt, size, n)
            return image_url
        except:
            return FallbackMessages.IMAGE_GENERATOR_TOOL_FALLBACK_MESSAGE