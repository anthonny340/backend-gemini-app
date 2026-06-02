import os
import tempfile

from fastapi import UploadFile, HTTPException, status

FILE_MIME_TYPES_BY_EXTENSION = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
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
