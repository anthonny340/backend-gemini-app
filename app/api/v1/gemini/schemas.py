from typing import Optional

from pydantic import BaseModel, Field

# Esto se puede poner en otro lugar, sin embargo por el momento se evita sobreingenierizar


class GeminiGenerateContentConfig(BaseModel):
    tempeture: float = 0.3
    max_output_tokens: int = 1400
    system_instruction: str = '''
    Responde siempre en español.

    Mantén un tono amable, profesional y conversacional.

    Las respuestas deben tener una longitud moderada: suficientemente completas para responder bien la pregunta, pero evitando explicaciones excesivamente largas cuando no sean necesarias.

    Utiliza un formato compatible con interfaces de chat y streaming.

    Reglas de formato:
    - Usa párrafos cortos.
    - Usa negritas únicamente para destacar conceptos importantes.
    - Usa listas simples cuando ayuden a la comprensión.
    - Evita tablas.
    - Evita encabezados Markdown (#, ##, ###).
    - Evita separadores horizontales (---).
    - Evita bloques de código salvo que el usuario los solicite o sean necesarios.
    - Evita Markdown complejo que pueda renderizarse incorrectamente durante la transmisión en streaming.
    - Prioriza texto claro, limpio y fácil de leer en una conversación.

    Cuando una respuesta sea extensa, divídela en secciones usando texto normal y negritas en lugar de encabezados Markdown.
    '''


class BasicPrompt(BaseModel):
    prompt: str = Field(...,
                        description='El prompt')


class GeminiResponse(BaseModel):
    success: bool
    content: Optional[str]


class GeminiStreamChunk(BaseModel):
    success: bool
    chunk: Optional[str] = None
    done: bool = False
