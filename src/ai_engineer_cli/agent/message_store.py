import json
from pathlib import Path

from ai_engineer_cli.agent.message import Message


class MessageStore:
    """
    JSON-based conversation storage.

    Stores and loads conversation history between CLI runs.
    """

    def __init__(
        self,
        conversation_id: str,
        base_dir: str = ".agent_data/conversations",
    ) -> None:
        self.conversation_id = conversation_id
        self.base_dir = Path(base_dir)
        self.file_path = self.base_dir / f"{conversation_id}.json"

    def load_messages(self) -> list[Message]:
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        raw_messages = data.get("messages", [])

        return [Message.from_dict(message) for message in raw_messages]

    def save_messages(self, messages: list[Message]) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "conversation_id": self.conversation_id,
            "messages": [message.to_dict() for message in messages],
        }

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        if self.file_path.exists():
            self.file_path.unlink()