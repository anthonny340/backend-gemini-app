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
    gemini = GeminiService()
    response = gemini.generate_content(prompt=content.prompt)

    response = response.model_dump(exclude_none=True)

    return response
