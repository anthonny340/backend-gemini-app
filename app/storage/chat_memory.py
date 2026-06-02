# Migrar a una BD

from typing import Any


class ChatMemory:
    def __init__(self):
        self.sessions: dict[str, Any] = {}
        self.messages: dict[str, list[dict[str, str]]] = {}

    def get_session(self, chat_id: str) -> Any | None:
        return self.sessions.get(chat_id)

    def get_session_info(self, chat_id: str) -> dict[str, Any]:
        session = self.get_session(chat_id)

        if session is None:
            return {
                "exists": False,
                "chat_id": chat_id,
                "message": "No existe una sesión",
            }

        return {
            "exists": True,
            "chat_id": chat_id,
            "session_type": type(session).__name__,
        }

    def get_or_create_session(self, chat_id: str, session_factory) -> Any:
        if chat_id not in self.sessions:
            self.sessions[chat_id] = session_factory()
            self.messages[chat_id] = []

        return self.sessions[chat_id]

    def add_message(self, chat_id: str, role: str, content: str) -> None:
        self.messages.setdefault(chat_id, []).append({
            "user": role,
            "content": content,
        })

    def get_messages(self, chat_id: str) -> dict[str, Any]:
        return {
            "chat_id": chat_id,
            "messages": self.messages.get(chat_id, []),
        }

    def clear(self, chat_id: str) -> None:
        self.sessions.pop(chat_id, None)
        self.messages.pop(chat_id, None)


chat_session = ChatMemory()
