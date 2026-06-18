from dataclasses import dataclass

from ai_engineer_cli.agent.message import Message


@dataclass(frozen=True)
class ContextTokenStats:
    current_request_tokens: int
    history_tokens: int
    full_context_tokens: int
    history_messages_count: int
    full_context_messages_count: int


class TokenBudget:
    """
    Estimates token usage for agent context.

    This is an approximation layer.
    Real input/output token usage is still taken from the LLM API response.
    """

    def __init__(self, chars_per_token: float = 4.0) -> None:
        self.chars_per_token = chars_per_token

    def estimate_text_tokens(self, text: str) -> int:
        if not text:
            return 0

        return max(1, int(len(text) / self.chars_per_token))

    def estimate_message_tokens(self, message: Message) -> int:
        role_overhead_tokens = 4
        return self.estimate_text_tokens(message.content) + role_overhead_tokens

    def estimate_messages_tokens(self, messages: list[Message]) -> int:
        return sum(self.estimate_message_tokens(message) for message in messages)

    def build_context_stats(
        self,
        current_request: Message,
        history: list[Message],
        full_context: list[Message],
    ) -> ContextTokenStats:
        return ContextTokenStats(
            current_request_tokens=self.estimate_message_tokens(current_request),
            history_tokens=self.estimate_messages_tokens(history),
            full_context_tokens=self.estimate_messages_tokens(full_context),
            history_messages_count=len(history),
            full_context_messages_count=len(full_context),
        )