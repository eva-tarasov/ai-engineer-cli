from ai_engineer_cli.agent.message import Message


class SlidingWindowStrategy:
    def __init__(self, recent_messages: int) -> None:
        self.recent_messages = recent_messages

    def build_context(
        self,
        system_prompt: str | None,
        history: list[Message],
        user_message: Message,
        summary: str | None = None,
        facts: dict[str, str] | None = None,
    ) -> list[Message]:
        messages: list[Message] = []

        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))

        recent_history = history[-self.recent_messages :]
        messages.extend(recent_history)
        messages.append(user_message)

        return messages