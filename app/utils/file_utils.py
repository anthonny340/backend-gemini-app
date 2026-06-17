import io
import os
import tempfile

from fastapi import UploadFile, HTTPException, status
from PIL import Image, UnidentifiedImageError

FILE_MIME_TYPES_BY_EXTENSION = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

IMAGE_FORMAT_EXTENSION = {
    "JPEG": "jpg",
    "PNG": "png",
    "GIF": "gif",
    "WEBP": "webp",
    "BMP": "bmp",
    "TIFF": "tiff",
}


def get_file_extension(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ""

    return filename.rsplit(".", 1)[-1].lower()


def resolve_mime_type(file: UploadFile) -> str:
    file_extension = get_file_extension(file.filename)
    file_mime_type = FILE_MIME_TYPES_BY_EXTENSION.get(file_extension, "")

    content_type = file.content_type or ""

    if content_type == "application/octet-stream":
        return file_mime_type

    return content_type


def get_image_file_extension(image_format: str) -> str:
    return IMAGE_FORMAT_EXTENSION.get(image_format.upper(), "")


def validate_image_content(content: bytes, filename: str) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(content))
        image.load()
        return image
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo {filename} no es una imagen válida.",
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo procesar la imagen {filename}: {str(error)}",
        )


def resolve_image_extension(image: Image.Image, filename: str) -> str:
    image_format = image.format or get_file_extension(filename).upper()

    file_extension = (
        get_image_file_extension(image_format)
        or get_file_extension(filename)
    )

    if not file_extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo determinar la extensión de la imagen {filename}.",
        )

    return file_extension


def upload_image_to_gemini(
    gemini_client,
    content: bytes,
    filename: str,
    mime_type: str,
    file_extension: str,
):
    suffix = f".{file_extension}"

    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        return gemini_client.files.upload(
            file=temp_file_path,
            config={
                "mime_type": mime_type,
                "display_name": filename,
            },
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir la imagen {filename}: {str(error)}",
        )

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


async def prepare_images_for_gemini(
    gemini_client,
    files: list[UploadFile],
):
    """Valida y prepara imágenes para que Gemini pueda leer y modificar el contenido."""
    prepared_files = []

    for file in files:
        await file.seek(0)

        mime_type = resolve_mime_type(file)

        if not mime_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archivo no válido para Gemini: {file.filename}. Se esperaba una imagen.",
            )

        content = await file.read()

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo no tiene nombre.",
            )
        image = validate_image_content(content, file.filename)
        file_extension = resolve_image_extension(image, file.filename)

        uploaded_file = upload_image_to_gemini(
            gemini_client=gemini_client,
            content=content,
            filename=file.filename,
            mime_type=mime_type,
            file_extension=file_extension,
        )

        prepared_files.append(uploaded_file)

        await file.seek(0)

    return prepared_files


async def upload_files(
    gemini_client,
    files: list[UploadFile],
):
    uploaded_files = []

    for file in files:
        mime_type = resolve_mime_type(file)

        if not mime_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se pudo determinar el MIME type de {file.filename}",
            )

        suffix = os.path.splitext(file.filename or "")[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            uploaded_file = gemini_client.files.upload(
                file=temp_file_path,
                config={
                    "mime_type": mime_type,
                    "display_name": file.filename,
                },
            )

            uploaded_files.append(uploaded_file)

        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al subir el archivo {file.filename}: {str(error)}",
            )

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return uploaded_files
