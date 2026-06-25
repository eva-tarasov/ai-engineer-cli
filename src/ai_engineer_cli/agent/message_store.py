import json
from pathlib import Path

from ai_engineer_cli.agent.conversation_config import ConversationConfig
from ai_engineer_cli.agent.message import Message


class MessageStore:
    """
    JSON-based conversation storage.

    One file stores one conversation:
    - config
    - summary
    - facts
    - messages
    - branches
    """

    def __init__(
        self,
        conversation_id: str,
        base_dir: str = ".agent_data/conversations",
    ) -> None:
        self.conversation_id = conversation_id
        self.base_dir = Path(base_dir)
        self.file_path = self.base_dir / f"{conversation_id}.json"

    def exists(self) -> bool:
        return self.file_path.exists()

    def load_config(self) -> ConversationConfig:
        data = self._load_data()
        return ConversationConfig.from_dict(data.get("config"))

    def save_config(self, config: ConversationConfig) -> None:
        data = self._load_data()
        data["conversation_id"] = self.conversation_id
        data["config"] = config.to_dict()
        self._save_data(data)

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
        return summary or None

    def save_summary(self, summary: str | None) -> None:
        data = self._load_data()
        data["conversation_id"] = self.conversation_id
        data["summary"] = summary
        self._save_data(data)

    def load_facts(self) -> dict[str, str]:
        data = self._load_data()
        facts = data.get("facts", {})
        return facts if isinstance(facts, dict) else {}

    def save_facts(self, facts: dict[str, str]) -> None:
        data = self._load_data()
        data["conversation_id"] = self.conversation_id
        data["facts"] = facts
        self._save_data(data)

    def load_branch_messages(self, branch_id: str) -> list[Message]:
        data = self._load_data()
        branches = data.get("branches", {})
        branch = branches.get(branch_id, {})
        raw_messages = branch.get("messages", [])

        return [Message.from_dict(message) for message in raw_messages]

    def save_branch_messages(self, branch_id: str, messages: list[Message]) -> None:
        data = self._load_data()
        branches = data.setdefault("branches", {})

        branch = branches.setdefault(
            branch_id,
            {
                "parent": None,
                "checkpoint_message_index": None,
                "messages": [],
            },
        )

        branch["messages"] = [message.to_dict() for message in messages]
        self._save_data(data)

    def create_branch(
        self,
        branch_id: str,
        from_branch_id: str = "main",
    ) -> None:
        data = self._load_data()
        branches = data.setdefault("branches", {})

        if branch_id in branches:
            raise ValueError(f"Branch already exists: {branch_id}")

        if from_branch_id == "main":
            source_messages = data.get("messages", [])
        else:
            source_branch = branches.get(from_branch_id)

            if source_branch is None:
                raise ValueError(f"Source branch does not exist: {from_branch_id}")

            source_messages = source_branch.get("messages", [])

        branches[branch_id] = {
            "parent": from_branch_id,
            "checkpoint_message_index": len(source_messages),
            "messages": source_messages,
        }

        self._save_data(data)

    def list_branches(self) -> list[str]:
        data = self._load_data()
        branches = data.get("branches", {})
        return sorted(branches.keys())

    def clear(self) -> None:
        """
        Clear runtime state but preserve conversation config.
        """
        data = self._load_data()
        data["conversation_id"] = self.conversation_id
        data["summary"] = None
        data["facts"] = {}
        data["messages"] = []
        data["branches"] = {
            "main": {
                "parent": None,
                "checkpoint_message_index": 0,
                "messages": [],
            }
        }
        self._save_data(data)

    def delete(self) -> None:
        """
        Delete the whole conversation file, including config, summary, facts, branches, and messages.
        """
        if self.file_path.exists():
            self.file_path.unlink()

    def _load_data(self) -> dict:
        if not self.file_path.exists():
            return {
                "conversation_id": self.conversation_id,
                "config": ConversationConfig().to_dict(),
                "summary": None,
                "facts": {},
                "messages": [],
                "branches": {
                    "main": {
                        "parent": None,
                        "checkpoint_message_index": 0,
                        "messages": [],
                    }
                },
            }

        with self.file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        data.setdefault("conversation_id", self.conversation_id)
        data.setdefault("config", ConversationConfig().to_dict())
        data.setdefault("summary", None)
        data.setdefault("facts", {})
        data.setdefault("messages", [])
        data.setdefault(
            "branches",
            {
                "main": {
                    "parent": None,
                    "checkpoint_message_index": 0,
                    "messages": [],
                }
            },
        )

        return data

    def _save_data(self, data: dict) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)