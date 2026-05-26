from typing import Optional

from pydantic import BaseModel, Field

# Esto se puede poner en otro lugar, sin embargo por el momento se evita sobreingenierizar


class GeminiGenerateContentConfig(BaseModel):
    tempeture: float = 0.3
    max_output_tokens: int = 1800
    system_instruction: str = "Respondeme únicamente en español, en formato markdown"


class BasicPrompt(BaseModel):
    prompt: str = Field(...,
                        description='El prompt')


class GeminiResponse(BaseModel):
    success: bool
    content: Optional[str]
    error: Optional[str]
