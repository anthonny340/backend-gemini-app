

from io import BytesIO
import os
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from google import genai
from google.genai.types import GenerateContentConfig
from PIL import Image
from google.api_core import exceptions
from collections.abc import AsyncGenerator
from app.api.v1.gemini.schemas import GeminiGenerateContentConfig, GeminiResponse, GeminiStreamChunk


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
                return GeminiResponse(success=False, content=None)

            return GeminiResponse(success=True, content=response.text)
        except exceptions.ResourceExhausted:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit / quota excedida")

        except exceptions.InvalidArgument:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Contenido inválido")

        except exceptions.Unauthenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials were not provided")

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )

    async def generate_content_stream(self, prompt: str, files: list[UploadFile] = [], model: str = "gemini-3.5-flash") -> AsyncGenerator[GeminiStreamChunk, None]:
        try:
            gemini_images = []
            if files:
                for uploaded_file in files:
                    image_bytes = await uploaded_file.read()
                    try:
                        image_stream = BytesIO(image_bytes)
                        gemini_image = Image.open(image_stream)
                        gemini_images.append(gemini_image)
                    except Exception:
                        raise HTTPException(
                            status_code=400,
                            detail=f"{uploaded_file.filename} no es una imagen válida"
                        )

            response = self.client.models.generate_content_stream(
                model=model,
                contents=[prompt, *gemini_images],
                config=self.config
            )

            for chunk in response:
                text = getattr(chunk, "text", None)

                if text:
                    yield GeminiStreamChunk(
                        success=True,
                        chunk=text,
                        done=False
                    )

            yield GeminiStreamChunk(
                success=True,
                done=True
            )

        except exceptions.ResourceExhausted:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit / quota excedida")

        except exceptions.InvalidArgument:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Contenido inválido")

        except exceptions.Unauthenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials were not provided")

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}"
            )
