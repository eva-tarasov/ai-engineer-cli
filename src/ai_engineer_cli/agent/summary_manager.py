from pathlib import Path

from ai_engineer_cli.agent.message import Message
from ai_engineer_cli.llm_client import LLMClient


DEFAULT_SUMMARY_PROMPT_PATH = Path(
    "src/ai_engineer_cli/prompts/summarize_history.md"
)


class SummaryManager:
    """
    Creates and updates conversation summaries.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_path: Path = DEFAULT_SUMMARY_PROMPT_PATH,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_path = prompt_path

    def summarize(
        self,
        messages: list[Message],
        existing_summary: str | None = None,
        model: str | None = None,
        max_output_tokens: int | None = 700,
        temperature: float | None = None,
    ) -> str:
        if not messages:
            return existing_summary or ""

        system_prompt = self._load_summary_prompt()
        prompt = self._build_summary_prompt(
            messages=messages,
            existing_summary=existing_summary,
        )

        response = self.llm_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )

        return response.text.strip()

    def _load_summary_prompt(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8")

    def _build_summary_prompt(
        self,
        messages: list[Message],
        existing_summary: str | None,
    ) -> str:
        parts: list[str] = []

        if existing_summary:
            parts.append("Existing summary:")
            parts.append(existing_summary)
            parts.append("")

        parts.append("New messages to summarize:")
        parts.append("")

        for message in messages:
            parts.append(f"{message.role.upper()}: {message.content}")

        parts.append("")
        parts.append("Update the summary using the existing summary and new messages.")

        return "\n".join(parts)