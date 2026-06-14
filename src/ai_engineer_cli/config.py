import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    api_key: str
    model: str


def load_config() -> Config:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. "
            "Create a .env file and add OPENAI_API_KEY=your_api_key_here"
        )

    return Config(
        api_key=api_key,
        model=model,
    )