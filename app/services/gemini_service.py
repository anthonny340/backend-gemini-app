

import os
from typing import Optional
from uuid import UUID, uuid4
from dotenv import load_dotenv

from fastapi import HTTPException, UploadFile, status
from google import genai
from google.genai.types import GenerateContentConfig
from PIL import Image
from google.api_core import exceptions
from collections.abc import AsyncGenerator
from app.api.v1.gemini.schemas import GeminiGenerateContentConfig, GeminiResponse, GeminiStreamChunk
from app.storage.chat_memory import chat_session
from app.utils.file_utils import prepare_images_for_gemini, upload_files
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads" / "images"
ALLOWED_IMAGE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class GeminiService:

    def __init__(self, geminiConfig: Optional[GeminiGenerateContentConfig] = None) -> None:

        if geminiConfig is None:
            geminiConfig = GeminiGenerateContentConfig()

        self.client = gemini_client
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

    async def generate_content_stream(self, prompt: str, files: Optional[list[UploadFile]] = None, model: str = "gemini-3.5-flash") -> AsyncGenerator[GeminiStreamChunk, None]:
        try:
            gemini_images = []
            if files:
                gemini_images = await upload_files(
                    gemini_client=gemini_client, files=files)

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
                        type="text",
                        chunk=text,
                        done=False
                    )

            yield GeminiStreamChunk(
                success=True,
                type='end',
                done=True
            )

        except exceptions.ResourceExhausted:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_429_TOO_MANY_REQUESTS - Rate limit / quota excedida",
                done=True
            )
        except exceptions.InvalidArgument:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_400_BAD_REQUEST - Contenido inválido",
                done=True
            )
        except exceptions.Unauthenticated:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_401_UNAUTHORIZED - Authentication credentials were not provided",
                done=True
            )
        except Exception as e:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk=f"status.HTTP_500_INTERNAL_SERVER_ERROR - Unexpected error: {str(e)}",
                done=True
            )

    async def generate_chat_content_stream(self, chatId: UUID, prompt: str, files: Optional[list[UploadFile]] = None, model: str = "gemini-3.5-flash") -> AsyncGenerator[GeminiStreamChunk, None]:
        try:
            gemini_images = []
            if files:
                gemini_images = await upload_files(
                    gemini_client=gemini_client, files=files)

            chat = chat_session.get_or_create_session(
                chat_id=str(chatId),
                session_factory=lambda: self.client.chats.create(
                    model=model,
                    config=self.config,
                ),
            )

            response = chat.send_message_stream(
                [prompt, *gemini_images]
            )

            chat_session.add_message(chat_id=str(
                chatId), role="User", content=prompt)

            full_text_response = ""

            for chunk in response:
                text = getattr(chunk, "text", None)

                if text:
                    full_text_response += text

                    yield GeminiStreamChunk(
                        success=True,
                        type="text",
                        chunk=text,
                        done=False
                    )

            chat_session.add_message(chat_id=str(
                chatId), role="Gemini", content=full_text_response)

            yield GeminiStreamChunk(
                success=True,
                type='end',
                done=True
            )
        except exceptions.ResourceExhausted:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_429_TOO_MANY_REQUESTS - Rate limit / quota excedida",
                done=True
            )
        except exceptions.InvalidArgument:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_400_BAD_REQUEST - Contenido inválido",
                done=True
            )
        except exceptions.Unauthenticated:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_401_UNAUTHORIZED - Authentication credentials were not provided",
                done=True
            )
        except Exception as e:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk=f"status.HTTP_500_INTERNAL_SERVER_ERROR - Unexpected error: {str(e)}",
                done=True
            )

    async def generate_chat_image_stream(self, chatId: UUID, prompt: str, files: Optional[list[UploadFile]] = None, model: str = "gemini-3.5-flash") -> AsyncGenerator[GeminiStreamChunk, None]:
        try:
            gemini_images = []
            if files:
                gemini_images = await prepare_images_for_gemini(
                    gemini_client=gemini_client, files=files)

            chat = chat_session.get_or_create_session(
                chat_id=str(chatId),
                session_factory=lambda: self.client.chats.create(
                    model=model,
                    config=self.config,
                ),
            )

            response = chat.send_message_stream(
                [prompt, *gemini_images]
            )

            chat_session.add_message(chat_id=str(
                chatId), role="User", content=prompt)

            full_text_response = ""

            for chunk in response:
                text = getattr(chunk, "text", None)

                if text:
                    full_text_response += text

                    yield GeminiStreamChunk(
                        success=True,
                        type="text",
                        chunk=text,
                        done=False
                    )

            image_response = await self.generate_image(prompt=prompt, gemini_images=gemini_images)

            yield image_response

            chat_session.add_message(chat_id=str(
                chatId), role="Gemini", content=full_text_response)

            yield GeminiStreamChunk(
                success=True,
                type='end',
                done=True
            )

        except exceptions.ResourceExhausted:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_429_TOO_MANY_REQUESTS - Rate limit / quota excedida",
                done=True
            )
        except exceptions.InvalidArgument:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_400_BAD_REQUEST - Contenido inválido",
                done=True
            )
        except exceptions.Unauthenticated:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk="status.HTTP_401_UNAUTHORIZED - Authentication credentials were not provided",
                done=True
            )
        except Exception as e:
            yield GeminiStreamChunk(
                success=False,
                type="error",
                chunk=f"status.HTTP_500_INTERNAL_SERVER_ERROR - Unexpected error: {str(e)}",
                done=True
            )

    async def generate_image(self, prompt: str, gemini_images: Optional[list] = None) -> GeminiStreamChunk:
        try:
            if gemini_images is None:
                gemini_images = []
            else:
                gemini_images = await prepare_images_for_gemini(
                    gemini_client=gemini_client, files=gemini_images)

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt, *gemini_images],
            )
            candidates = response.candidates or []

            for candidate in candidates:
                content = candidate.content
                if content is None or content.parts is None:
                    continue

                for part in content.parts:
                    inline_data = part.inline_data
                    if inline_data is None or inline_data.data is None:
                        continue

                    # Controlando el tipo de imagen
                    mime_type = inline_data.mime_type
                    mime_type = mime_type or 'No support'
                    extension = ALLOWED_IMAGE_TYPES.get(
                        mime_type.lower())

                    if extension is None:
                        return GeminiStreamChunk(
                            success=False,
                            type="error",
                            chunk=f"Tipo de imagen no soportado: {mime_type}",
                            done=True,
                        )

                    filename = f"{uuid4()}.{extension}"
                    file_path = UPLOAD_DIR / filename
                    with open(file_path, "wb") as file:
                        file.write(inline_data.data)

                    image_url = f"{os.getenv("API_URL")}/static/images/{filename}"

                    return GeminiStreamChunk(
                        success=True,
                        type="image",
                        mime_type=inline_data.mime_type,
                        chunk=image_url,
                        done=False,
                    )
            return GeminiStreamChunk(
                success=False,
                type="error",
                chunk="No genero la imagen",
                done=False,
            )
        except HTTPException as http_exc:
            return GeminiStreamChunk(
                success=False,
                type="error",
                chunk=f"status.HTTP_{http_exc.status_code} - {http_exc.detail}",
                done=True
            )
        except Exception as e:
            return GeminiStreamChunk(
                success=False,
                type="error",
                chunk=f"status.HTTP_500_INTERNAL_SERVER_ERROR - Unexpected error: {str(e)}",
                done=True
            )
