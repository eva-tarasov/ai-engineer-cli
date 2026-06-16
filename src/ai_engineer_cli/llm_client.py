import time
from dataclasses import dataclass

from openai import OpenAI

from ai_engineer_cli.config import Config
from ai_engineer_cli.model_pricing import estimate_cost_usd


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    duration_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: float | None

def supports_temperature(model: str) -> bool:
    return not model.startswith("gpt-5")

class LLMClient:
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.api_key)

    def ask(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        selected_model = model or self.config.model

        input_messages = []

        if system_prompt:
            input_messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        input_messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        request_params = {
            "model": selected_model,
            "input": input_messages,
        }

        if max_output_tokens is not None:
            request_params["max_output_tokens"] = max_output_tokens

        if temperature is not None and supports_temperature(selected_model):
            request_params["temperature"] = temperature

        start_time = time.perf_counter()
        response = self.client.responses.create(**request_params)
        duration_seconds = time.perf_counter() - start_time

        usage = getattr(response, "usage", None)

        input_tokens = getattr(usage, "input_tokens", None) if usage else None
        output_tokens = getattr(usage, "output_tokens", None) if usage else None
        total_tokens = getattr(usage, "total_tokens", None) if usage else None

        estimated_cost_usd = estimate_cost_usd(
            model=selected_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return LLMResponse(
            text=response.output_text,
            model=selected_model,
            duration_seconds=duration_seconds,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )
