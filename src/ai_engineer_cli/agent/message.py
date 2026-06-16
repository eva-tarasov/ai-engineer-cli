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