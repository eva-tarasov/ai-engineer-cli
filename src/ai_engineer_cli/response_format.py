import json
from enum import Enum


class ResponseFormat(str, Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"


def build_system_prompt(
    response_format: ResponseFormat,
    max_output_tokens: int | None = None,
    stop_instruction: str | None = None,
) -> str:
    instructions: list[str] = [
        "You are a helpful engineering assistant.",
        "Keep the answer clear, practical, and technically accurate.",
    ]

    if response_format == ResponseFormat.TEXT:
        instructions.append("Answer in plain text.")

    elif response_format == ResponseFormat.MARKDOWN:
        instructions.append(
            "Answer in clean Markdown. Use headings and bullet points when useful."
        )

    elif response_format == ResponseFormat.JSON:
        instructions.extend(
            [
                "Return only valid JSON.",
                "Do not include Markdown.",
                "Do not wrap the JSON in code fences.",
                'Use this structure: {"summary": string, "key_points": [string], "example": string}',
            ]
        )

    else:
        raise ValueError(f"Unsupported response format: {response_format}")

    if max_output_tokens is not None:
        instructions.append(
            f"Limit the answer to approximately {max_output_tokens} output tokens."
        )

    if stop_instruction:
        instructions.append(stop_instruction)

    return " ".join(instructions)


def validate_json_response(response_text: str) -> dict:
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"Model returned invalid JSON: {error}") from error

    if not isinstance(parsed, dict):
        raise ValueError("Model returned JSON, but the root value is not an object.")

    return parsed