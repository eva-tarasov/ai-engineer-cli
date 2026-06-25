import json
from pathlib import Path

from ai_engineer_cli.agent.message import Message
from ai_engineer_cli.llm_client import LLMClient


DEFAULT_FACTS_PROMPT_PATH = Path(
    "src/ai_engineer_cli/prompts/extract_facts.md"
)


class FactsManager:
    """
    Extracts and updates durable key-value facts from conversation messages.

    Facts extraction is an auxiliary mechanism.
    If facts parsing fails, the agent must continue with existing facts.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_path: Path = DEFAULT_FACTS_PROMPT_PATH,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_path = prompt_path

    def update_facts(
        self,
        existing_facts: dict[str, str],
        messages: list[Message],
        model: str | None = None,
        max_output_tokens: int | None = 1200,
        temperature: float | None = None,
    ) -> dict[str, str]:
        if not messages:
            return existing_facts

        system_prompt = self.prompt_path.read_text(encoding="utf-8")
        prompt = self._build_prompt(
            existing_facts=existing_facts,
            messages=messages,
        )

        response = self.llm_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )

        parsed = self._parse_facts_response(response.text)

        if parsed is None:
            return existing_facts

        return self._normalize_facts(parsed)

    def _build_prompt(
        self,
        existing_facts: dict[str, str],
        messages: list[Message],
    ) -> str:
        parts: list[str] = []

        parts.append("Existing facts:")
        parts.append(json.dumps(existing_facts, ensure_ascii=False, indent=2))
        parts.append("")
        parts.append("New messages:")
        parts.append("")

        for message in messages:
            parts.append(f"{message.role.upper()}: {message.content}")

        parts.append("")
        parts.append("Return the updated facts JSON object.")
        parts.append("Return JSON only.")

        return "\n".join(parts)

    def _parse_facts_response(self, text: str) -> dict | None:
        cleaned_text = text.strip()

        if not cleaned_text:
            return None

        parsed = self._try_parse_json(cleaned_text)

        if parsed is not None:
            return parsed

        extracted_json = self._extract_json_object(cleaned_text)

        if extracted_json is None:
            return None

        return self._try_parse_json(extracted_json)

    def _try_parse_json(self, text: str) -> dict | None:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        return parsed

    def _extract_json_object(self, text: str) -> str | None:
        start_index = text.find("{")
        end_index = text.rfind("}")

        if start_index == -1 or end_index == -1:
            return None

        if end_index <= start_index:
            return None

        return text[start_index : end_index + 1]

    def _normalize_facts(self, facts: dict) -> dict[str, str]:
        normalized_facts: dict[str, str] = {}

        for key, value in facts.items():
            normalized_key = str(key).strip()

            if not normalized_key:
                continue

            normalized_value = str(value).strip()

            if not normalized_value:
                continue

            normalized_facts[normalized_key] = normalized_value[:300]

        return normalized_facts