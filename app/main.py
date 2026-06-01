from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from app.api.v1.gemini.schemas import BasicPrompt
from app.services.gemini_service import GeminiService
load_dotenv()

app = FastAPI(title='Backend Gemini')


@app.get('/')
def home():
    return {'message': 'Bienvenidos: by Anthonny Sacheri'}


@app.post('/api/basic-prompt')
def basicPrompt(
    content: BasicPrompt
):
    """
    Genera una respuesta utilizando el modelo Gemini
    a partir del prompt enviado por el usuario.

    Args:
        content (BasicPrompt):
            Contiene el prompt que será procesado por Gemini.

    Returns:
        dict:
            Respuesta generada por el modelo.

            Ejemplo:
            {
                "success": true,
                "content": "Respuesta generada..."
            }

    Raises:
        Exception:
            Si ocurre un error durante la generación
            de contenido con Gemini.
    """
    gemini = GeminiService()
    response = gemini.generate_content(prompt=content.prompt)

    return response


@app.post('/api/basic-prompt-stream')
async def basicPromptStream(
    content: BasicPrompt
):
    """
    Genera una respuesta de Gemini en streaming mediante Server-Sent Events.

    Cada evento emitido posee la siguiente estructura:

        {
            "success": bool,
            "chunk": str | null,
            "done": bool,
            "error": str | null
        }

    Args:
        content (BasicPrompt):
            Prompt enviado por el usuario.

    Returns:
        StreamingResponse:
            Flujo SSE que transmite los fragmentos generados por Gemini
            hasta que la respuesta finaliza o se produce un error.
    """
    gemini = GeminiService()

    async def event_generator():
        async for chunk in gemini.generate_content_stream(prompt=content.prompt):
            # yield chunk.model_dump_json() + "\n"
            yield f"data:{chunk.model_dump_json()}\n\n"

    return StreamingResponse(content=event_generator(), media_type="text/event-stream")


@app.post('/api/basic-prompt-stream-images')
async def basicPromptStreamImages(
    prompt: str = Form(...),
    images: Annotated[list[UploadFile] | None, File()] = None
):
    """
    Genera una respuesta de Gemini en streaming mediante Server-Sent Events.

    Cada evento emitido posee la siguiente estructura:

        {
            "success": bool,
            "chunk": str | null,
            "done": bool,
            "error": str | null
        }

    Args:
        prompt: str = Form(...):
            Prompt enviado por el usuario.
        images: Annotated[list[UploadFile], File()] = []
            Imagenes enviadas por el usuario

    Returns:
        StreamingResponse:
            Flujo SSE que transmite los fragmentos generados por Gemini
            hasta que la respuesta finaliza o se produce un error.
    """
    gemini = GeminiService()
    images = images or []

    async def event_generator():
        async for chunk in gemini.generate_content_stream(prompt=prompt, files=images):
            yield f"data:{chunk.model_dump_json()}\n\n"

    return StreamingResponse(content=event_generator(), media_type="text/event-stream")
