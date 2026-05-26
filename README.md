## Requisitos

- Python 3.10 o superior
- Poetry instalado

Verificar versiones:

```bash
python --version
poetry --version
```

# Dev

1. Clonar repositorio
2. Crear .env basado en el .env.template
3. Cambiar las variables de entorno
4. Instalar dependencia con el comando ```poetry install```
5. Ejecutar con proyecto con el siguiente comando:
```
poetry run fastapi dev app/main.py
```