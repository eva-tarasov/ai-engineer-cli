from openai import OpenAI

from ai_engineer_cli.config import Config


class LLMClient:
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.api_key)

    def ask(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        if system_prompt:
            input_messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        else:
            input_messages = prompt

        request_params = {
            "model": self.config.model,
            "input": input_messages,
        }

        if max_output_tokens is not None:
            request_params["max_output_tokens"] = max_output_tokens

        response = self.client.responses.create(**request_params)

        return response.output_text