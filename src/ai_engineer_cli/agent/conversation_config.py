from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ConversationConfig:
    agent: bool = False
    response_format: str = "text"
    language: str = "ru"
    show_context_stats: bool = False
    use_summary: bool = False
    summary_every: int = 10
    recent_messages: int = 6
    context_token_limit: int | None = None
    context_strategy: str = "full"
    branch_id: str = "main"
    model: str | None = None
    max_output_tokens: int | None = None
    temperature: float | None = None
    stop_instruction: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ConversationConfig":
        if not data:
            return cls()

        return cls(
            agent=data.get("agent", False),
            response_format=data.get("response_format", "text"),
            language=data.get("language", "ru"),
            show_context_stats=data.get("show_context_stats", False),
            use_summary=data.get("use_summary", False),
            summary_every=data.get("summary_every", 10),
            recent_messages=data.get("recent_messages", 6),
            context_token_limit=data.get("context_token_limit"),
            context_strategy=data.get("context_strategy", "full"),
            branch_id=data.get("branch_id", "main"),
            model=data.get("model"),
            max_output_tokens=data.get("max_output_tokens"),
            temperature=data.get("temperature"),
            stop_instruction=data.get("stop_instruction"),
        )