from fastapi import FastAPI

app = FastAPI(title='Backend Gemini')


@app.get('/')
def home():
    return {'message': 'Bienvenidos: by Anthonny Sacheri'}
