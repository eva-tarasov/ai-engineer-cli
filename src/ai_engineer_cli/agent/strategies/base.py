from typing import Protocol

from ai_engineer_cli.agent.message import Message


class ContextStrategy(Protocol):
    def build_context(
        self,
        system_prompt: str | None,
        history: list[Message],
        user_message: Message,
        summary: str | None = None,
        facts: dict[str, str] | None = None,
    ) -> list[Message]:
        ...