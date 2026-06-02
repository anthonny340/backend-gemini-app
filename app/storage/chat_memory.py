# Migrar a una BD

from typing import Any


class ChatMemory:
    def __init__(self):
        self.sessions: dict[str, Any] = {}

    def get_session(self, chat_id: str) -> Any | None:
        return self.sessions.get(chat_id)

    def get_or_create_session(self, chat_id: str, session_factory) -> Any:
        if chat_id not in self.sessions:
            self.sessions[chat_id] = session_factory()

        return self.sessions[chat_id]

    def clear(self, chat_id: str) -> None:
        self.sessions.pop(chat_id, None)


chat_session = ChatMemory()
