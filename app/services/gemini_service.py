

import os
from typing import Optional

from google import genai
from google.genai.types import GenerateContentConfig

from app.api.v1.gemini.schemas import GeminiGenerateContentConfig, GeminiResponse


class GeminiService:

    def __init__(self, geminiConfig: Optional[GeminiGenerateContentConfig] = None) -> None:

        if geminiConfig is None:
            geminiConfig = GeminiGenerateContentConfig()

        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.config = GenerateContentConfig(
            temperature=geminiConfig.tempeture,
            max_output_tokens=geminiConfig.max_output_tokens,
            system_instruction=geminiConfig.system_instruction,
        )

    def generate_content(self, prompt: str, model: str = "gemini-3.5-flash") -> GeminiResponse:
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
                config=self.config
            )

            if not response.text:
                return GeminiResponse(success=False, content=None, error="Gemini returned an empty response")

            return GeminiResponse(success=True, content=response.text, error=None)
        except Exception as e:
            return GeminiResponse(
                success=False,
                content=None,
                error=str(e)
            )
