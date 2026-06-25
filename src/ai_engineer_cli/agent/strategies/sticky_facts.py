from ai_engineer_cli.agent.message import Message


class StickyFactsStrategy:
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

        if facts:
            facts_text = "\n".join(
                f"- {key}: {value}" for key, value in sorted(facts.items())
            )

            messages.append(
                Message(
                    role="system",
                    content=f"Sticky facts:\n{facts_text}",
                )
            )

        recent_history = history[-self.recent_messages :]
        messages.extend(recent_history)
        messages.append(user_message)

        return messages