from typing import Dict, Any, List
from pydantic import BaseModel, Field
from .base_agent import BaseAgent, AgentState
import re
from PIL import Image
import io
import base64
from langchain_core.output_parsers import PydanticOutputParser

class ImageValidationResult(BaseModel):
    """Structured output for image validation"""
    is_valid_ui: bool = Field(description="Whether the image is a valid UI design")
    confidence: float = Field(description="Confidence score of the validation")
    reason: str = Field(description="Reason for the validation result")

class InputAgent(BaseAgent[ImageValidationResult]):
    def __init__(self):
        super().__init__("input_agent", model_name="gpt-4o")
        self.figma_url_pattern = r'^https://(?:www\.)?figma\.com/file/[a-zA-Z0-9]+/.*$'
        
        # Set up output parser
        parser = PydanticOutputParser(pydantic_object=ImageValidationResult)
        self.set_output_parser(parser)
    
    def validate_input(self, state: AgentState) -> bool:
        input_data = state.input_data
        if not input_data:
            state.error = "No input data provided"
            return False
            
        if "figma_url" in input_data:
            if not re.match(self.figma_url_pattern, input_data["figma_url"]):
                state.error = "Invalid Figma URL format"
                return False
        elif "image" in input_data:
            try:
                # Validate if the image data is valid
                image_data = input_data["image"]
                if isinstance(image_data, str):
                    # Handle base64 encoded image
                    # Add padding if necessary
                    padding = 4 - (len(image_data) % 4)
                    if padding != 4:
                        image_data += '=' * padding
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data
                Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                state.error = f"Invalid image data: {str(e)}"
                return False
        else:
            state.error = "Neither Figma URL nor image data provided"
            return False
            
        return True
    
    async def _validate_ui_image(self, image_data: bytes) -> ImageValidationResult:
        """Validate if the image is a valid UI design using GPT-4 Vision"""
        prompt = """
    You are an expert UI design analyzer. Given an image, your job is to determine whether the image is a UI design.

    Please analyze the image and return ONLY a valid JSON object (no markdown, no explanation) matching this format:

    {
    "is_valid_ui": true,
    "confidence": 0.92,
    "reason": "The image contains UI elements like buttons and navigation typical of a UI mockup."
    }

    Strictly follow:
    - `is_valid_ui`: true or false
    - `confidence`: float between 0 and 1
    - `reason`: concise explanation

    Output nothing else. Only valid JSON.
    """

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"{image_data}"
                        }
                    }
                ]
            }
        ]

        # Get model response
        response = await self.model.ainvoke(messages)

        # Optional: Strip surrounding whitespace
        raw_output = response.content.strip()

        # Try parsing with detailed error feedback
        try:
            return self.output_parser.parse(raw_output)
        except Exception as e:
            raise ValueError(f"Output parsing failed: {e}\nRaw output: {raw_output}")

    
    async def process(self, state: AgentState) -> AgentState:
        # if not self.validate_input(state):
        #     return state
            
        if "image" in state.input_data:
            # Handle image input
            image_data = state.input_data["image"]
            # if isinstance(image_data, str):
            #     image_bytes = base64.b64decode(image_data)
            # else:
            #     image_bytes = image_data
                
            # Validate UI image
            validation_result = await self._validate_ui_image(image_data)
            
            if not validation_result.is_valid_ui:
                state.error = f"Invalid UI image: {validation_result.reason}"
                return state
            
            # Store validation metadata
            state.metadata["validation"] = validation_result.dict()
            
            # Process the input and prepare it for the next agent
            processed_data = {
                "type": "image",
                "raw_input": state.input_data,
            }
        else:
            # Handle Figma URL (placeholder for now)
            processed_data = {
                "type": "figma",
                "raw_input": state.input_data
            }
        
        state.output_data = processed_data
        return state 