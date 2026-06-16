from dataclasses import dataclass
from typing import Literal


MessageRole = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: MessageRole
    content: str

    def to_dict(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Message":
        role = data.get("role")
        content = data.get("content")

        if role not in ("system", "user", "assistant"):
            raise ValueError(f"Unsupported message role: {role}")

        if content is None:
            raise ValueError("Message content is required.")

        return cls(
            role=role,
            content=content,
        )