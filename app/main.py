from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.v1.gemini.schemas import BasicPrompt
from app.services.gemini_service import GeminiService
from google.genai.types import GenerateContentConfig
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

    response = response.model_dump(exclude_none=True)

    return response
