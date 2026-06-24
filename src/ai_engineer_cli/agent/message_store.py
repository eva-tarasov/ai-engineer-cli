import json
from pathlib import Path

from ai_engineer_cli.agent.message import Message


class MessageStore:
    """
    JSON-based conversation storage.

    Stores and loads conversation history and summary between CLI runs.
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
        data = self._load_data()
        raw_messages = data.get("messages", [])

        return [Message.from_dict(message) for message in raw_messages]

    def save_messages(self, messages: list[Message]) -> None:
        data = self._load_data()
        data["conversation_id"] = self.conversation_id
        data["messages"] = [message.to_dict() for message in messages]

        self._save_data(data)

    def load_summary(self) -> str | None:
        data = self._load_data()
        summary = data.get("summary")

        if not summary:
            return None

        return summary

    def save_summary(self, summary: str | None) -> None:
        data = self._load_data()
        data["conversation_id"] = self.conversation_id
        data["summary"] = summary

        self._save_data(data)

    def clear(self) -> None:
        if self.file_path.exists():
            self.file_path.unlink()

    def _load_data(self) -> dict:
        if not self.file_path.exists():
            return {
                "conversation_id": self.conversation_id,
                "summary": None,
                "messages": [],
            }

        with self.file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _save_data(self, data: dict) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)