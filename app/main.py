from dotenv import load_dotenv
from fastapi import FastAPI
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
    Genera una respuesta Stream utilizando el modelo Gemini
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

    async def event_generator():
        async for chunk in gemini.generate_content_stream(prompt=content.prompt):
            yield chunk.model_dump_json() + "\n"
            # yield f"data: {chunk.model_dump_json()}\n\n"

    return StreamingResponse(content=event_generator(), media_type="text/plain")
