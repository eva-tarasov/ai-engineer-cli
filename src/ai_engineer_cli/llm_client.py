from openai import OpenAI

from ai_engineer_cli.config import Config


class LLMClient:
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.api_key)

    def ask(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.config.model,
            input=prompt,
        )

        return response.output_text