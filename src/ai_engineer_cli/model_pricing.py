from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPrice:
    input_per_1m: float
    output_per_1m: float


MODEL_PRICES: dict[str, ModelPrice] = {
    # Approximate OpenAI API prices in USD per 1M tokens.
    # Check official pricing docs periodically.
    "gpt-5-nano": ModelPrice(input_per_1m=0.05, output_per_1m=0.40),
    "gpt-5-mini": ModelPrice(input_per_1m=0.25, output_per_1m=2.00),
    "gpt-5": ModelPrice(input_per_1m=1.25, output_per_1m=10.00),
}


def estimate_cost_usd(
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    price = MODEL_PRICES.get(model)

    if price is None:
        return None

    if input_tokens is None or output_tokens is None:
        return None

    input_cost = input_tokens / 1_000_000 * price.input_per_1m
    output_cost = output_tokens / 1_000_000 * price.output_per_1m

    return input_cost + output_cost